from __future__ import annotations

from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import hashlib
import hmac
import json
import sys

import numpy as np
import pandas as pd
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from narcis.attacks import attack_suite
from narcis.benchmark import benchmark_workload, derive_subkey
from narcis.coding import bits_to_symbols, encode_payload, encode_payload_rs
from narcis.data import discover_images
from narcis.group_bank import build_balanced_group_bank
from narcis.group_bank_projection import select_group_bank_projection
from narcis.group_bank_protocol import encode_group_bank, majority_failure_signatures
from narcis.index import CoverIndex
from narcis.protocol import NarcisProtocol, Transmission, keyed_permutation
from narcis.security import (
    PAYLOAD_ID,
    ReplayGuard,
    SessionMetadata,
    open_metadata,
    seal_metadata,
)
from run_bossbase_campaign import (
    CALIBRATION_ATTACKS,
    NativeImageDataset,
    dataset_statistics,
    embed_dataset,
    train_encoder,
)

HOLDOUT_ATTACKS = (
    "gaussian_9_holdout",
    "gaussian_15_holdout",
    "blur_1.2_holdout",
    "blur_1.8_holdout",
    "crop_08_holdout",
    "crop_12_holdout",
    "rotate_5_holdout",
    "rotate_9_holdout",
)

EXPECTED_CHECKPOINT_SHA256 = {
    11: "0adac1e014b799ada4a46698bcad922ce4ce116697186c1d45964e405a81e28c",
    29: "658e97d5fe4ad8da03ebad42461bce458d967beaf5753ac5d22a3c62eb480f2e",
    47: "426d058567fbb08eca9a34668c1a20caeb29ba8d5c7b6ba0d2e8c44c449c6a2a",
    71: "e0e958faf040a4d080d377a7694ea86cd602eab7c5350d4f04e619ca37fcade4",
    101: "810f843f82cd6726b16ae632d38ec6bb0f1dbfaaf0345ffd92a6a0a883cb722e",
}

SENDER = "arcis-sender"
RECEIVER = "arcis-receiver"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_identifiers(paths: list[Path], dataset_root: Path) -> list[str]:
    root = dataset_root.resolve()
    identifiers = [path.resolve().relative_to(root).as_posix() for path in paths]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("canonical identifiers are not unique")
    return identifiers


def decode_attack(
    protocol: NarcisProtocol,
    transmission: Transmission,
    received_labels: np.ndarray,
    encryption_key: bytes,
    metadata: SessionMetadata,
    plaintext: bytes,
) -> tuple[bool, int, float]:
    intended = np.asarray(
        [protocol.cover_index.labels[path] for path in transmission.covers],
        dtype=int,
    )
    try:
        recovered_envelope, corrections = protocol.decode_labels(
            received_labels.tolist(),
            metadata.padding_bits,
            sequence=metadata.sequence,
        )
        nonce, ciphertext = recovered_envelope[:12], recovered_envelope[12:]
        associated = PAYLOAD_ID + metadata.sequence.to_bytes(8, "big")
        recovered = AESGCM(encryption_key).decrypt(nonce, ciphertext, associated)
        success = recovered == plaintext
    except Exception:
        corrections = -1
        success = False
    return bool(success), int(corrections), float(np.mean(received_labels == intended))


def authenticated_control_roundtrip(
    transmission: Transmission,
    sequence: int,
    metadata_key: bytes,
    replay_guard: ReplayGuard,
    exercise_negative_tests: bool = False,
) -> tuple[SessionMetadata, int, dict[str, bool]]:
    metadata = SessionMetadata(
        sequence=int(sequence),
        padding_bits=int(transmission.padding_bits),
        codebook_size=int(transmission.codebook_size),
        cover_count=len(transmission.covers),
    )
    envelope = seal_metadata(metadata, metadata_key, SENDER, RECEIVER)
    opened = open_metadata(envelope, metadata_key, SENDER, RECEIVER, replay_guard)
    if opened != metadata:
        raise RuntimeError("authenticated metadata roundtrip changed metadata")
    if opened.codebook_size != transmission.codebook_size:
        raise RuntimeError("authenticated metadata codebook size mismatch")
    if opened.cover_count != len(transmission.covers):
        raise RuntimeError("authenticated metadata cover count mismatch")

    checks = {"tamper_rejected": True, "replay_rejected": True}
    if exercise_negative_tests:
        tampered = bytearray(envelope)
        tampered[-1] ^= 1
        try:
            open_metadata(bytes(tampered), metadata_key, SENDER, RECEIVER, ReplayGuard())
            checks["tamper_rejected"] = False
        except InvalidTag:
            pass

        try:
            open_metadata(envelope, metadata_key, SENDER, RECEIVER, replay_guard)
            checks["replay_rejected"] = False
        except ValueError as error:
            if "Replay" not in str(error):
                raise
    return opened, len(envelope), checks


def random_group_bank(
    labels: np.ndarray,
    label_count: int,
    group_size: int,
    seed: int,
) -> dict[int, tuple[tuple[int, ...], ...]]:
    rng = np.random.default_rng(seed)
    banks = {}
    for label in range(label_count):
        positions = np.flatnonzero(labels == label).astype(int)
        rng.shuffle(positions)
        usable = (len(positions) // group_size) * group_size
        positions = positions[:usable]
        banks[label] = tuple(
            tuple(int(value) for value in positions[start : start + group_size])
            for start in range(0, usable, group_size)
        )
    return banks


def encode_group_bank_uniform_scheduler(
    protocol: NarcisProtocol,
    payload: bytes,
    sequence: int,
    identifiers: list[str],
    banks: dict[int, tuple[tuple[int, ...], ...]],
) -> Transmission:
    coded = (
        encode_payload(payload)
        if protocol.fec == "hamming"
        else encode_payload_rs(payload, protocol.rs_parity)
    )
    symbols, padding = bits_to_symbols(coded, protocol.bits_per_symbol)
    permutation = protocol._permutation(sequence)
    labels = [permutation[symbol] for symbol in symbols]
    demand = Counter(labels)
    context = protocol._selection_context(payload, sequence)

    orders: dict[int, list[int]] = {}
    for label, count in demand.items():
        rows = []
        label_bytes = int(label).to_bytes(4, "big", signed=False)
        for group_index, group in enumerate(banks[label]):
            membership = b"|".join(
                identifiers[position].encode("utf-8") for position in sorted(group)
            )
            digest = hmac.new(
                protocol.selection_key,
                b"uniform-group:" + context + label_bytes + membership,
                hashlib.sha256,
            ).digest()
            rows.append((digest, group_index))
        rows.sort()
        if count > len(rows):
            raise ValueError(f"group capacity exhausted for label {label}")
        orders[label] = [group_index for _, group_index in rows[:count]]

    cursors = Counter()
    selected: list[str] = []
    used_positions: set[int] = set()
    for label in labels:
        group = banks[label][orders[label][cursors[label]]]
        cursors[label] += 1
        members = sorted(
            group,
            key=lambda position: hmac.new(
                protocol.selection_key,
                b"member:"
                + context
                + int(label).to_bytes(4, "big", signed=False)
                + identifiers[position].encode("utf-8"),
                hashlib.sha256,
            ).digest(),
        )
        for position in members:
            if position in used_positions:
                raise RuntimeError("cover reuse detected in uniform-scheduler ablation")
            used_positions.add(position)
            selected.append(identifiers[position])
    return Transmission(
        covers=selected,
        padding_bits=padding,
        codebook_size=protocol.codebook_size,
        repetition=protocol.repetition,
        fec=protocol.fec,
    )


class FixedMappingProtocol(NarcisProtocol):
    def _permutation(self, sequence: int) -> list[int]:
        return keyed_permutation(self.codebook_size, self.mapping_key, sequence=0)


def evaluate_holdout_variant(
    *,
    name: str,
    protocol: NarcisProtocol,
    encoder,
    workload,
    identifiers: list[str],
    positions: dict[str, int],
    predicted: dict[str, np.ndarray],
    encryption_key: bytes,
    metadata_key: bytes,
) -> tuple[pd.DataFrame, dict]:
    rows = []
    cover_frequency = np.zeros(len(identifiers), dtype=int)
    label_frequency = np.zeros(protocol.codebook_size, dtype=int)
    guard = ReplayGuard()
    metadata_bytes = []
    for message in workload:
        transmission = encoder(message)
        selected = np.asarray([positions[path] for path in transmission.covers], dtype=int)
        if len(np.unique(selected)) != len(selected):
            raise RuntimeError(f"{name}: cover reuse within session {message.sequence}")
        metadata, control_bytes, _ = authenticated_control_roundtrip(
            transmission,
            message.sequence,
            metadata_key,
            guard,
        )
        metadata_bytes.append(control_bytes)
        cover_frequency[selected] += 1
        for path in transmission.covers:
            label_frequency[protocol.cover_index.labels[path]] += 1
        for attack_name in HOLDOUT_ATTACKS:
            success, corrections, accuracy = decode_attack(
                protocol,
                transmission,
                np.asarray(predicted[attack_name][selected], dtype=int),
                encryption_key,
                metadata,
                message.plaintext,
            )
            rows.append(
                {
                    "variant": name,
                    "sequence": int(message.sequence),
                    "payload_bytes": int(message.payload_bytes),
                    "attack": attack_name,
                    "success": bool(success),
                    "rs_corrections": int(corrections),
                    "cover_label_accuracy": float(accuracy),
                    "covers": len(selected),
                    "metadata_bytes": int(control_bytes),
                }
            )
    frame = pd.DataFrame(rows)
    summary = {
        "variant": name,
        "holdout_trials": int(len(frame)),
        "holdout_successes": int(frame["success"].sum()),
        "holdout_success_rate": float(frame["success"].mean()),
        "mean_cover_label_accuracy": float(frame["cover_label_accuracy"].mean()),
        "unique_covers": int(np.count_nonzero(cover_frequency)),
        "cover_frequency_cv": float(cover_frequency.std() / max(cover_frequency.mean(), 1e-12)),
        "label_emission_cv": float(label_frequency.std() / max(label_frequency.mean(), 1e-12)),
        "mean_metadata_bytes": float(np.mean(metadata_bytes)),
        "by_attack": {
            attack: {
                "trials": int(len(part)),
                "successes": int(part["success"].sum()),
                "success_rate": float(part["success"].mean()),
                "mean_cover_label_accuracy": float(part["cover_label_accuracy"].mean()),
            }
            for attack, part in frame.groupby("attack")
        },
    }
    return frame, summary


def symbol_cluster_cycle_coverage(protocol: NarcisProtocol) -> dict:
    return {
        str(symbol): len(
            {
                protocol._permutation(sequence)[symbol]
                for sequence in range(protocol.codebook_size)
            }
        )
        for symbol in range(protocol.codebook_size)
    }


def main() -> None:
    parser = ArgumentParser(description="Aligned final ARCIS Caltech-101 channel recheck and component ablation")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True, choices=tuple(EXPECTED_CHECKPOINT_SHA256))
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--component-ablation", action="store_true")
    args = parser.parse_args()

    dataset_root = args.dataset_root.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    args.checkpoint_root.mkdir(parents=True, exist_ok=True)

    paths = discover_images(dataset_root)
    if len(paths) < 8500:
        raise ValueError(f"Caltech-101 requires >=8500 images, found {len(paths)}")
    order = np.random.default_rng(args.seed).permutation(len(paths))
    train_paths = [paths[position] for position in order[:1500]]
    index_paths = [paths[position] for position in order[1500:8500]]
    dataset = NativeImageDataset(index_paths, "RGB", 256)
    identifiers = canonical_identifiers(index_paths, dataset_root)

    model, history = train_encoder(
        train_paths,
        args.seed,
        args.epochs,
        128,
        64,
        args.output,
        checkpoint_root=args.checkpoint_root,
        input_mode="RGB",
        channel_size=256,
    )
    checkpoint = args.checkpoint_root / f"encoder_seed_{args.seed}.pt"
    checkpoint_sha = sha256_file(checkpoint)
    if history:
        pd.DataFrame(history).to_csv(args.output / "training_history.csv", index=False)

    clean, _, clean_seconds = embed_dataset(model, dataset, 128)
    suite = attack_suite(256, args.seed)
    all_attack_names = CALIBRATION_ATTACKS + HOLDOUT_ATTACKS
    attacked = {}
    attack_seconds = {}
    for attack_name in all_attack_names:
        values, _, seconds = embed_dataset(model, dataset, 128, suite[attack_name])
        attacked[attack_name] = values
        attack_seconds[attack_name] = seconds
        print(f"embedded attack {attack_name}", flush=True)
    visual = dataset_statistics(dataset)

    calibration = {name: attacked[name] for name in CALIBRATION_ATTACKS}
    choice, candidates = select_group_bank_projection(
        clean,
        calibration,
        visual,
        clusters=8,
        group_size=5,
        principal_components=16,
        random_directions=32,
        random_seed=20260828 + args.seed,
    )
    candidates.to_csv(args.output / "projection_candidates.csv", index=False)
    banks, diagnostics = build_balanced_group_bank(
        choice.labels,
        choice.calibration_correct,
        label_count=8,
        group_size=5,
        seed=20260830 + args.seed,
        restarts=10,
        swap_steps=6000,
    )
    signatures = majority_failure_signatures(banks, choice.calibration_correct)
    index = CoverIndex.build(identifiers, choice.labels)
    master_key, encryption_key, workload = benchmark_workload("Caltech-101", args.seed)
    metadata_key = derive_subkey(master_key, b"metadata-aead")
    protocol = NarcisProtocol(index, 8, master_key, repetition=5, fec="reed_solomon", rs_parity=128)
    positions = {identifier: position for position, identifier in enumerate(identifiers)}
    predicted = {name: choice.codebook.predict(values) for name, values in attacked.items()}

    raw_rows = []
    schedule_rows = []
    target = np.zeros((len(identifiers), len(workload)), dtype=np.uint8)
    replay_guard = ReplayGuard()
    control_negative_checks = None
    metadata_lengths = []
    for message in workload:
        transmission = encode_group_bank(
            protocol,
            message.envelope,
            sequence=message.sequence,
            identifiers=identifiers,
            banks=banks,
            signatures=signatures,
        )
        metadata, metadata_bytes, negative_checks = authenticated_control_roundtrip(
            transmission,
            message.sequence,
            metadata_key,
            replay_guard,
            exercise_negative_tests=message.sequence == 0,
        )
        if message.sequence == 0:
            control_negative_checks = negative_checks
        metadata_lengths.append(metadata_bytes)
        selected = np.asarray([positions[path] for path in transmission.covers], dtype=int)
        if len(np.unique(selected)) != len(selected):
            raise RuntimeError(f"cover reuse within session {message.sequence}")
        target[selected, message.sequence] = 1
        for position in selected:
            schedule_rows.append(
                {
                    "image_index": int(position),
                    "image_id": identifiers[int(position)],
                    "sequence": int(metadata.sequence),
                    "payload_bytes": int(message.payload_bytes),
                }
            )
        for attack_name in all_attack_names:
            success, corrections, accuracy = decode_attack(
                protocol,
                transmission,
                np.asarray(predicted[attack_name][selected], dtype=int),
                encryption_key,
                metadata,
                message.plaintext,
            )
            raw_rows.append(
                {
                    "dataset": "Caltech-101",
                    "resampling_seed": args.seed,
                    "sequence": int(metadata.sequence),
                    "payload_bytes": int(message.payload_bytes),
                    "attack": attack_name,
                    "attack_family": "calibration" if attack_name in CALIBRATION_ATTACKS else "holdout",
                    "success": bool(success),
                    "rs_corrections": int(corrections),
                    "cover_label_accuracy": float(accuracy),
                    "covers": len(selected),
                    "metadata_bytes": int(metadata_bytes),
                }
            )

    if control_negative_checks != {"tamper_rejected": True, "replay_rejected": True}:
        raise RuntimeError(f"control-plane negative checks failed: {control_negative_checks}")

    schedule = pd.DataFrame(schedule_rows).sort_values(["sequence", "image_index"], kind="stable").reset_index(drop=True)
    schedule_path = args.output / "schedule.csv"
    if schedule_path.exists():
        existing = pd.read_csv(schedule_path).sort_values(["sequence", "image_index"], kind="stable").reset_index(drop=True)
        comparable = ["image_index", "image_id", "sequence", "payload_bytes"]
        if not schedule[comparable].equals(existing[comparable]):
            raise RuntimeError("channel recheck schedule differs from detector-audit schedule")
    else:
        schedule.to_csv(schedule_path, index=False)
    np.save(args.output / "session_target.npy", target)

    raw = pd.DataFrame(raw_rows)
    raw.to_csv(args.output / "channel_recheck_raw.csv", index=False)
    grouped = (
        raw.groupby(["attack_family", "attack", "payload_bytes"], as_index=False)
        .agg(
            trials=("success", "size"),
            successes=("success", "sum"),
            success_rate=("success", "mean"),
            mean_cover_label_accuracy=("cover_label_accuracy", "mean"),
            minimum_cover_label_accuracy=("cover_label_accuracy", "min"),
            maximum_rs_corrections=("rs_corrections", "max"),
        )
    )
    grouped.to_csv(args.output / "channel_recheck_summary.csv", index=False)

    family_summary = {}
    for family in ("calibration", "holdout"):
        subset = raw[raw["attack_family"] == family]
        family_summary[family] = {
            "trials": int(len(subset)),
            "successes": int(subset["success"].sum()),
            "success_rate": float(subset["success"].mean()),
            "maximum_rs_corrections": int(subset["rs_corrections"].max()),
            "minimum_cover_label_accuracy": float(subset["cover_label_accuracy"].min()),
        }

    ablation_summary = None
    if args.component_ablation:
        random_banks = random_group_bank(choice.labels, 8, 5, 20260919 + args.seed)
        random_signatures = majority_failure_signatures(random_banks, choice.calibration_correct)
        fixed_protocol = FixedMappingProtocol(index, 8, master_key, repetition=5, fec="reed_solomon", rs_parity=128)
        variants = [
            ("arcis_full", protocol, lambda m: encode_group_bank(protocol, m.envelope, m.sequence, identifiers, banks, signatures)),
            ("random_groups", protocol, lambda m: encode_group_bank(protocol, m.envelope, m.sequence, identifiers, random_banks, random_signatures)),
            ("uniform_group_scheduler", protocol, lambda m: encode_group_bank_uniform_scheduler(protocol, m.envelope, m.sequence, identifiers, banks)),
            ("fixed_mapping", fixed_protocol, lambda m: encode_group_bank(fixed_protocol, m.envelope, m.sequence, identifiers, banks, signatures)),
            ("matched_bucket_baseline", protocol, lambda m: protocol.encode(m.envelope, sequence=m.sequence)),
        ]
        ablation_frames = []
        summaries = {}
        for name, variant_protocol, encoder in variants:
            frame, summary = evaluate_holdout_variant(
                name=name,
                protocol=variant_protocol,
                encoder=encoder,
                workload=workload,
                identifiers=identifiers,
                positions=positions,
                predicted=predicted,
                encryption_key=encryption_key,
                metadata_key=metadata_key,
            )
            frame["resampling_seed"] = args.seed
            ablation_frames.append(frame)
            summaries[name] = summary
            print(json.dumps(summary, indent=2), flush=True)
        ablation_raw = pd.concat(ablation_frames, ignore_index=True)
        ablation_raw.to_csv(args.output / "component_ablation_raw.csv", index=False)
        ablation_summary = {
            "resampling_seed": args.seed,
            "variants": summaries,
            "cyclic_symbol_cluster_coverage": symbol_cluster_cycle_coverage(protocol),
            "fixed_symbol_cluster_coverage": symbol_cluster_cycle_coverage(fixed_protocol),
        }
        (args.output / "component_ablation_summary.json").write_text(
            json.dumps(ablation_summary, indent=2, allow_nan=False),
            encoding="utf-8",
        )

    manifest = {
        "dataset": "Caltech-101",
        "resampling_seed": args.seed,
        "split_definition": {
            "source_images": len(paths),
            "train_images": 1500,
            "index_images": 7000,
            "within_run_train_index_disjoint": True,
            "cross_seed_independence_claimed": False,
        },
        "checkpoint_expected_sha256": EXPECTED_CHECKPOINT_SHA256[args.seed],
        "checkpoint_actual_sha256": checkpoint_sha,
        "checkpoint_matches_recorded_fresh_campaign": checkpoint_sha == EXPECTED_CHECKPOINT_SHA256[args.seed],
        "projection": {
            "name": choice.name,
            "family": choice.family,
            "stable_images": int(choice.stable.sum()),
            "stable_fraction": float(choice.stable.mean()),
            "max_unavoidable_bad_fraction": float(choice.max_unavoidable_bad_fraction),
            "sum_unavoidable_bad_fraction": float(choice.sum_unavoidable_bad_fraction),
        },
        "group_bank_all_labels_reach_lower_bound": bool(all(item.reaches_lower_bound for item in diagnostics)),
        "schedule": {
            "sessions": len(workload),
            "all_index_covers_used": bool(np.all(target.sum(axis=1) > 0)),
            "minimum_sessions_per_cover": int(target.sum(axis=1).min()),
            "maximum_sessions_per_cover": int(target.sum(axis=1).max()),
            "total_cover_emissions": int(target.sum()),
        },
        "authenticated_control_plane": {
            "sender": SENDER,
            "receiver": RECEIVER,
            "metadata_fields": ["sequence", "padding_bits", "codebook_size", "cover_count"],
            "mean_metadata_envelope_bytes": float(np.mean(metadata_lengths)),
            "tamper_rejected": bool(control_negative_checks["tamper_rejected"]),
            "replay_rejected": bool(control_negative_checks["replay_rejected"]),
        },
        "channel": family_summary,
        "component_ablation": ablation_summary,
        "timing": {
            "clean_embedding_seconds": clean_seconds,
            "attack_embedding_seconds": attack_seconds,
        },
        "artifacts": {
            "schedule_csv_sha256": sha256_file(schedule_path),
            "session_target_npy_sha256": sha256_file(args.output / "session_target.npy"),
            "channel_recheck_raw_csv_sha256": sha256_file(args.output / "channel_recheck_raw.csv"),
            "channel_recheck_summary_csv_sha256": sha256_file(args.output / "channel_recheck_summary.csv"),
            **(
                {
                    "component_ablation_raw_csv_sha256": sha256_file(args.output / "component_ablation_raw.csv"),
                    "component_ablation_summary_json_sha256": sha256_file(args.output / "component_ablation_summary.json"),
                }
                if args.component_ablation
                else {}
            ),
        },
    }
    (args.output / "channel_recheck_manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=True), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, allow_nan=True), flush=True)


if __name__ == "__main__":
    main()
