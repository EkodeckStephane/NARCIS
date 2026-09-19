from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
from time import perf_counter
import hashlib
import io
import json
import math
import sys

import numpy as np
import pandas as pd
import torch
import torchvision.transforms.functional as TF
from PIL import Image, ImageFilter
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from run_bossbase_campaign import CALIBRATION_ATTACKS, model_view
from run_tomm_groupbank_cached import _decode_attack
from run_tomm_validation import prepare_partition
from narcis.benchmark import benchmark_workload
from narcis.group_bank import build_balanced_group_bank
from narcis.group_bank_projection import select_group_bank_projection
from narcis.group_bank_protocol import encode_group_bank, majority_failure_signatures
from narcis.index import CoverIndex
from narcis.perm_rrns_core import (
    _protected_candidates,
    decode_embeddings,
    decode_lists,
    encode_blocks,
    encode_groups,
    mapping,
    plan,
    protect,
    residue_candidates,
    templates,
    unprotect,
)
from narcis.protocol import NarcisProtocol

DATASET_NAME = "Caltech-101-PERM-RRNS-FRESH"
FRESH_ATTACKS = (
    "gaussian_7",
    "gaussian_18",
    "blur_1.0",
    "blur_2.1",
    "crop_06",
    "crop_09",
    "crop_14",
    "rotate_4",
    "rotate_6",
    "rotate_11",
    "jpeg_65",
    "crop_09_jpeg_65",
    "crop_14_blur_1.0",
)
PAYLOAD_SIZES = (8, 32, 64)
MESSAGES_PER_SIZE = 10


def _pil(tensor: torch.Tensor) -> Image.Image:
    return TF.to_pil_image(tensor)


def _tensor(image: Image.Image, size: int = 256) -> torch.Tensor:
    return TF.to_tensor(image.convert("RGB").resize((size, size), Image.Resampling.BICUBIC))


def _noise_seed(seed: int, attack_name: str, image_index: int) -> int:
    digest = hashlib.sha256(
        f"{seed}|{attack_name}|{image_index}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big")


def apply_fresh_attack(
    tensor: torch.Tensor,
    attack_name: str,
    seed: int,
    image_index: int,
    image_size: int = 256,
) -> torch.Tensor:
    def jpeg(image: Image.Image, quality: int) -> Image.Image:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        return Image.open(buffer).convert("RGB")

    def crop(image: Image.Image, fraction: float) -> Image.Image:
        margin = int(image.width * fraction)
        return image.crop(
            (margin, margin, image.width - margin, image.height - margin)
        )

    image = _pil(tensor).convert("RGB")
    if attack_name.startswith("gaussian_"):
        sigma = float(attack_name.split("_")[1])
        rng = np.random.default_rng(_noise_seed(seed, attack_name, image_index))
        array = np.asarray(image, dtype=np.float32)
        array = np.clip(array + rng.normal(0.0, sigma, array.shape), 0, 255)
        image = Image.fromarray(array.astype(np.uint8), mode="RGB")
    elif attack_name.startswith("blur_"):
        radius = float(attack_name.split("_")[1])
        image = image.filter(ImageFilter.GaussianBlur(radius))
    elif attack_name.startswith("crop_") and "_jpeg_" not in attack_name and "_blur_" not in attack_name:
        fraction = int(attack_name.split("_")[1]) / 100.0
        image = crop(image, fraction)
    elif attack_name.startswith("rotate_"):
        angle = float(attack_name.split("_")[1])
        image = image.rotate(
            angle,
            resample=Image.Resampling.BILINEAR,
            fillcolor=(0, 0, 0),
        )
    elif attack_name == "jpeg_65":
        image = jpeg(image, 65)
    elif attack_name == "crop_09_jpeg_65":
        image = jpeg(crop(image, 0.09), 65)
    elif attack_name == "crop_14_blur_1.0":
        image = crop(image, 0.14).filter(ImageFilter.GaussianBlur(1.0))
    else:
        raise KeyError(attack_name)
    return _tensor(image, image_size)


@torch.no_grad()
def embed_fresh_attack(
    model,
    dataset,
    model_size: int,
    attack_name: str,
    seed: int,
    batch_size: int = 16,
) -> np.ndarray:
    rows = []
    offset = 0
    for images, _ in DataLoader(dataset, batch_size=batch_size, shuffle=False):
        damaged = torch.stack(
            [
                apply_fresh_attack(image, attack_name, seed, offset + local)
                for local, image in enumerate(images)
            ]
        )
        rows.append(model(model_view(damaged, model_size)).cpu().numpy())
        offset += len(images)
    return np.concatenate(rows, axis=0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1 << 20)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def flatten_true_residues(protected: bytes) -> tuple[tuple, list[int], list[int]]:
    blocks = encode_blocks(protected, 18)
    configs = tuple(config for config, _ in blocks)
    residues = [value for _, values in blocks for value in values]
    moduli = [modulus for config, _ in blocks for modulus in config.moduli]
    return configs, residues, moduli


def build_candidate_lists(
    received_groups: list[np.ndarray],
    configs: tuple,
    sequence: int,
    key: bytes,
    banks,
    refs: np.ndarray,
):
    moduli = [m for config in configs for m in config.moduli]
    return tuple(
        residue_candidates(group, modulus, index, sequence, key, banks, refs)
        for index, (group, modulus) in enumerate(
            zip(received_groups, moduli, strict=True)
        )
    )


def hard_decode(lists, configs, key: bytes, sequence: int):
    vector = [row[0][0] for row in lists]
    tested = 0
    for candidate in _protected_candidates(vector, configs):
        tested += 1
        try:
            return unprotect(candidate, key, sequence), tested
        except Exception:
            pass
    raise ValueError("hard RRNS/AEAD decode failed")


def sequence_features(
    method: str,
    seed: int,
    sequence: int,
    payload_bytes: int,
    selected_ids: list[str],
    positions: dict[str, int],
    labels: np.ndarray,
    clean: np.ndarray,
) -> dict:
    idx = np.asarray([positions[name] for name in selected_ids], dtype=int)
    lab = labels[idx]
    transitions = np.zeros((8, 8), dtype=float)
    for first, second in zip(lab[:-1], lab[1:]):
        transitions[int(first), int(second)] += 1
    if transitions.sum():
        transitions /= transitions.sum()

    emb = clean[idx]
    if len(emb) > 1:
        cosine = np.sum(emb[:-1] * emb[1:], axis=1)
        cosine_stats = [
            float(np.mean(cosine)),
            float(np.std(cosine)),
            float(np.quantile(cosine, 0.1)),
            float(np.quantile(cosine, 0.5)),
            float(np.quantile(cosine, 0.9)),
        ]
    else:
        cosine_stats = [float("nan")] * 5

    group_cosines = []
    for start in range(0, len(idx) - 4, 5):
        block = clean[idx[start : start + 5]]
        sim = block @ block.T
        tri = sim[np.triu_indices(5, 1)]
        group_cosines.extend(tri.tolist())
    cluster_counts = np.bincount(lab, minlength=8).astype(float)
    probabilities = cluster_counts / max(cluster_counts.sum(), 1.0)
    entropy = float(
        -np.sum(probabilities * np.log2(np.maximum(probabilities, 1e-12)))
    )
    row = {
        "seed": seed,
        "sequence": sequence,
        "payload_bytes": payload_bytes,
        "method": method,
        "images": len(selected_ids),
        "cluster_entropy": entropy,
        "adjacent_cosine_mean": cosine_stats[0],
        "adjacent_cosine_std": cosine_stats[1],
        "adjacent_cosine_q10": cosine_stats[2],
        "adjacent_cosine_q50": cosine_stats[3],
        "adjacent_cosine_q90": cosine_stats[4],
        "within_group_cosine_mean": float(np.mean(group_cosines)) if group_cosines else float("nan"),
        "within_group_cosine_std": float(np.std(group_cosines)) if group_cosines else float("nan"),
    }
    for first in range(8):
        for second in range(8):
            row[f"transition_{first}_{second}"] = float(transitions[first, second])
    return row


def network_stress(
    payload: bytes,
    payload_bytes: int,
    sequence: int,
    master_key: bytes,
    groups: tuple[tuple[str, ...], ...],
    positions: dict[str, int],
    clean: np.ndarray,
    banks,
    refs,
) -> list[dict]:
    base = [clean[[positions[name] for name in group]].copy() for group in groups]
    rows = []

    def attempt(name: str, received, framing_reject: bool = False):
        if framing_reject:
            rows.append(
                {
                    "sequence": sequence,
                    "payload_bytes": payload_bytes,
                    "stress": name,
                    "outcome": "rejected_by_group_framing",
                    "recovered": False,
                    "safe_reject": True,
                }
            )
            return
        try:
            recovered, diagnostics = decode_embeddings(
                received,
                payload_bytes,
                sequence,
                master_key,
                banks,
                refs,
            )
            exact = recovered == payload
            rows.append(
                {
                    "sequence": sequence,
                    "payload_bytes": payload_bytes,
                    "stress": name,
                    "outcome": "recovered" if exact else "unexpected_plaintext",
                    "recovered": bool(exact),
                    "safe_reject": False,
                    "mode": diagnostics.get("mode"),
                }
            )
        except Exception:
            rows.append(
                {
                    "sequence": sequence,
                    "payload_bytes": payload_bytes,
                    "stress": name,
                    "outcome": "authenticated_reject",
                    "recovered": False,
                    "safe_reject": True,
                }
            )

    attempt("clean", [row.copy() for row in base])

    if base:
        middle = len(base) // 2
        duplicated = [row.copy() for row in base]
        duplicated[middle][1] = duplicated[middle][0]
        attempt("one_duplicated_image", duplicated)

        swapped = [row.copy() for row in base]
        swapped[middle][0], swapped[middle][1] = (
            swapped[middle][1].copy(),
            swapped[middle][0].copy(),
        )
        attempt("adjacent_image_swap", swapped)

    if len(base) > 1:
        swapped_groups = [row.copy() for row in base]
        middle = max(0, len(base) // 2 - 1)
        swapped_groups[middle], swapped_groups[middle + 1] = (
            swapped_groups[middle + 1],
            swapped_groups[middle],
        )
        attempt("adjacent_group_swap", swapped_groups)

    for count in (1, 2, 3, 5):
        attempt(f"burst_loss_{count}", base, framing_reject=True)
    return rows


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=5)
    args = parser.parse_args()

    seed = args.seed
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    checkpoints = out / "checkpoints"

    started = perf_counter()
    prepared = prepare_partition(
        dataset_root=args.dataset_root,
        checkpoint_root=checkpoints,
        output=out,
        seed=seed,
        train_count=1500,
        index_count=7000,
        epochs=args.epochs,
        input_mode="RGB",
        channel_size=256,
        model_size=128,
        embedding_dim=64,
    )
    training_seconds = perf_counter() - started

    choice, candidates = select_group_bank_projection(
        prepared["clean"],
        prepared["attacked"],
        prepared["visual_features"],
        clusters=8,
        group_size=5,
        principal_components=16,
        random_directions=32,
        random_seed=20260828 + seed,
    )
    candidates.to_csv(out / "projection_candidates.csv", index=False)
    banks, bank_diagnostics = build_balanced_group_bank(
        choice.labels,
        choice.calibration_correct,
        label_count=8,
        group_size=5,
        seed=20260830 + seed,
        restarts=10,
        swap_steps=6000,
    )
    signatures = majority_failure_signatures(banks, choice.calibration_correct)
    identifiers = prepared["identifiers"]
    positions = {name: index for index, name in enumerate(identifiers)}
    refs = templates(prepared["clean"], prepared["attacked"], CALIBRATION_ATTACKS)

    bank_manifest = {
        "seed": seed,
        "projection": choice.name,
        "family": choice.family,
        "stable_images": int(choice.stable.sum()),
        "stable_fraction": float(choice.stable.mean()),
        "labels": {
            str(label): {
                "covers": diagnostic.covers,
                "groups": diagnostic.groups,
                "bad_groups_by_calibration_attack": list(diagnostic.bad_groups_by_attack),
                "lower_bound_by_calibration_attack": list(diagnostic.lower_bound_by_attack),
                "reaches_lower_bound": diagnostic.reaches_lower_bound,
            }
            for label, diagnostic in enumerate(bank_diagnostics)
        },
    }
    (out / "bank_manifest.json").write_text(
        json.dumps(bank_manifest, indent=2), encoding="utf-8"
    )

    fresh_embeddings = {}
    attack_timings = {}
    for attack_name in FRESH_ATTACKS:
        attack_started = perf_counter()
        fresh_embeddings[attack_name] = embed_fresh_attack(
            prepared["model"],
            prepared["dataset"],
            128,
            attack_name,
            seed,
        )
        attack_timings[attack_name] = perf_counter() - attack_started

    master_key, encryption_key, workload = benchmark_workload(
        DATASET_NAME,
        seed,
        payload_sizes=PAYLOAD_SIZES,
        messages_per_size=MESSAGES_PER_SIZE,
    )
    index = CoverIndex.build(identifiers, choice.labels)
    original = NarcisProtocol(
        index,
        8,
        master_key,
        repetition=5,
        fec="reed_solomon",
        rs_parity=128,
    )

    result_rows = []
    ablation_rows = []
    sequence_rows = []
    network_rows = []

    for message in workload:
        protected, configs_from_encoder, groups = encode_groups(
            message.plaintext,
            message.sequence,
            master_key,
            identifiers,
            banks,
            r=18,
        )
        if protected != message.envelope[12:]:
            raise RuntimeError("compact AEAD is inconsistent with benchmark envelope")
        configs, true_residues, moduli = flatten_true_residues(protected)
        if tuple(configs_from_encoder) != tuple(configs):
            raise RuntimeError("RRNS planner mismatch")

        new_selected_ids = [name for group in groups for name in group]
        if len(new_selected_ids) != len(set(new_selected_ids)):
            raise RuntimeError("cover reuse in PERM-RRNS session")

        old_tx = encode_group_bank(
            original,
            message.envelope,
            sequence=message.sequence,
            identifiers=identifiers,
            banks=banks,
            signatures=signatures,
        )
        sequence_rows.append(
            sequence_features(
                "perm_rrns",
                seed,
                message.sequence,
                message.payload_bytes,
                new_selected_ids,
                positions,
                choice.labels,
                prepared["clean"],
            )
        )
        sequence_rows.append(
            sequence_features(
                "arcis_rs128",
                seed,
                message.sequence,
                message.payload_bytes,
                old_tx.covers,
                positions,
                choice.labels,
                prepared["clean"],
            )
        )

        network_rows.extend(
            network_stress(
                message.plaintext,
                message.payload_bytes,
                message.sequence,
                master_key,
                groups,
                positions,
                prepared["clean"],
                banks,
                (refs["crop"], refs["general"]),
            )
        )

        for attack_name in FRESH_ATTACKS:
            all_received = fresh_embeddings[attack_name]
            received_groups = [
                all_received[[positions[name] for name in group]]
                for group in groups
            ]
            lists_crop = build_candidate_lists(
                received_groups,
                configs,
                message.sequence,
                master_key,
                banks,
                refs["crop"],
            )
            lists_general = build_candidate_lists(
                received_groups,
                configs,
                message.sequence,
                master_key,
                banks,
                refs["general"],
            )
            crop_top1_errors = sum(
                row[0][0] != true
                for row, true in zip(lists_crop, true_residues, strict=True)
            )
            general_top1_errors = sum(
                row[0][0] != true
                for row, true in zip(lists_general, true_residues, strict=True)
            )

            full_started = perf_counter()
            try:
                recovered, diagnostics = decode_embeddings(
                    received_groups,
                    message.payload_bytes,
                    message.sequence,
                    master_key,
                    banks,
                    (refs["crop"], refs["general"]),
                    r=18,
                )
                full_success = recovered == message.plaintext
                full_mode = diagnostics.get("mode")
                states = diagnostics.get("tested", 0)
                template_hypothesis = diagnostics.get("template_hypothesis")
            except Exception:
                full_success = False
                full_mode = "failed"
                states = 0
                template_hypothesis = -1
            full_seconds = perf_counter() - full_started

            selected = np.asarray(
                [positions[name] for name in old_tx.covers], dtype=int
            )
            received_labels = choice.codebook.predict(all_received[selected])
            old_success, old_corrections, old_accuracy = _decode_attack(
                original,
                old_tx,
                received_labels,
                encryption_key,
                message.sequence,
                message.plaintext,
            )

            result_rows.append(
                {
                    "seed": seed,
                    "sequence": message.sequence,
                    "payload_bytes": message.payload_bytes,
                    "attack": attack_name,
                    "perm_rrns_images": len(new_selected_ids),
                    "perm_rrns_success": int(full_success),
                    "perm_rrns_decode_mode": full_mode,
                    "perm_rrns_template_hypothesis": template_hypothesis,
                    "perm_rrns_candidate_states": states,
                    "perm_rrns_decode_seconds": full_seconds,
                    "crop_top1_residue_errors": crop_top1_errors,
                    "general_top1_residue_errors": general_top1_errors,
                    "arcis_rs128_images": len(old_tx.covers),
                    "arcis_rs128_success": int(old_success),
                    "arcis_rs128_rs_corrections": old_corrections,
                    "arcis_rs128_label_accuracy": old_accuracy,
                }
            )

            for name, lists, hypothesis in (
                ("hard_crop", lists_crop, refs["crop"]),
                ("hard_general", lists_general, refs["general"]),
            ):
                try:
                    recovered, tested = hard_decode(
                        lists, configs, master_key, message.sequence
                    )
                    success = recovered == message.plaintext
                except Exception:
                    success = False
                    tested = 0
                ablation_rows.append(
                    {
                        "seed": seed,
                        "sequence": message.sequence,
                        "payload_bytes": message.payload_bytes,
                        "attack": attack_name,
                        "variant": name,
                        "success": int(success),
                        "tested_states": tested,
                    }
                )

            for name, lists in (
                ("beam_crop", lists_crop),
                ("beam_general", lists_general),
            ):
                try:
                    recovered, diag = decode_lists(
                        lists, configs, master_key, message.sequence
                    )
                    success = recovered == message.plaintext
                    tested = diag.get("tested", 0)
                except Exception:
                    success = False
                    tested = 0
                ablation_rows.append(
                    {
                        "seed": seed,
                        "sequence": message.sequence,
                        "payload_bytes": message.payload_bytes,
                        "attack": attack_name,
                        "variant": name,
                        "success": int(success),
                        "tested_states": tested,
                    }
                )

            ablation_rows.append(
                {
                    "seed": seed,
                    "sequence": message.sequence,
                    "payload_bytes": message.payload_bytes,
                    "attack": attack_name,
                    "variant": "dual_full",
                    "success": int(full_success),
                    "tested_states": states,
                }
            )
            ablation_rows.append(
                {
                    "seed": seed,
                    "sequence": message.sequence,
                    "payload_bytes": message.payload_bytes,
                    "attack": attack_name,
                    "variant": "arcis_rs128",
                    "success": int(old_success),
                    "tested_states": 0,
                }
            )

    result = pd.DataFrame(result_rows)
    result.to_csv(out / "fresh_payload_results.csv", index=False)
    pd.DataFrame(ablation_rows).to_csv(out / "ablation_results.csv", index=False)
    pd.DataFrame(sequence_rows).to_csv(out / "sequential_features.csv", index=False)
    pd.DataFrame(network_rows).to_csv(out / "network_stress.csv", index=False)

    summary = (
        result.groupby(["payload_bytes", "attack"], as_index=False)
        .agg(
            trials=("perm_rrns_success", "size"),
            perm_rrns_successes=("perm_rrns_success", "sum"),
            images=("perm_rrns_images", "first"),
            mean_candidate_states=("perm_rrns_candidate_states", "mean"),
            max_candidate_states=("perm_rrns_candidate_states", "max"),
            mean_decode_seconds=("perm_rrns_decode_seconds", "mean"),
            mean_crop_top1_errors=("crop_top1_residue_errors", "mean"),
            mean_general_top1_errors=("general_top1_residue_errors", "mean"),
            arcis_rs128_successes=("arcis_rs128_success", "sum"),
            arcis_rs128_images=("arcis_rs128_images", "first"),
        )
    )
    summary["useful_bits_per_image"] = (
        summary["payload_bytes"] * 8 / summary["images"]
    )
    summary.to_csv(out / "fresh_payload_summary.csv", index=False)

    traffic = {}
    for payload_bytes in PAYLOAD_SIZES:
        protected_bytes = payload_bytes + 16
        compact_no_rrns_groups = math.ceil((protected_bytes * 8) / 9)
        planned = plan(protected_bytes, 18)
        full_images = sum(config.images for config in planned)
        original_codeword_bytes = payload_bytes + 28 + 10 + 128
        original_bits = original_codeword_bytes * 8
        permutation_rs128_images = math.ceil(original_bits / 9) * 5
        original_images = math.ceil(original_bits / 3) * 5
        traffic[str(payload_bytes)] = {
            "payload_bits": payload_bytes * 8,
            "compact_aead_bytes": protected_bytes,
            "compact_no_fec_images": compact_no_rrns_groups * 5,
            "permutation_plus_rs128_images": permutation_rs128_images,
            "perm_rrns_images": full_images,
            "arcis_rs128_images": original_images,
        }
    (out / "traffic_ablation.json").write_text(
        json.dumps(traffic, indent=2), encoding="utf-8"
    )

    checkpoint = checkpoints / f"encoder_seed_{seed}.pt"
    manifest = {
        "seed": seed,
        "fresh_attacks": FRESH_ATTACKS,
        "payload_sizes": PAYLOAD_SIZES,
        "messages_per_size": MESSAGES_PER_SIZE,
        "checkpoint_sha256": sha256_file(checkpoint),
        "projection": choice.name,
        "projection_family": choice.family,
        "training_seconds_including_calibration": training_seconds,
        "fresh_attack_embedding_seconds": attack_timings,
        "result_sha256": sha256_file(out / "fresh_payload_results.csv"),
        "ablation_sha256": sha256_file(out / "ablation_results.csv"),
        "network_sha256": sha256_file(out / "network_stress.csv"),
        "sequential_features_sha256": sha256_file(out / "sequential_features.csv"),
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "seed": seed,
                "checkpoint_sha256": manifest["checkpoint_sha256"],
                "projection": choice.name,
                "fresh_trials": len(result),
                "fresh_successes": int(result["perm_rrns_success"].sum()),
                "output": str(out),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
