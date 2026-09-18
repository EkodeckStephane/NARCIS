from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import hashlib
import json

import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from narcis.benchmark import benchmark_workload
from narcis.group_bank import build_balanced_group_bank
from narcis.group_bank_projection import select_group_bank_projection
from narcis.group_bank_protocol import encode_group_bank, majority_failure_signatures
from narcis.index import CoverIndex
from narcis.protocol import NarcisProtocol
from narcis.security import PAYLOAD_ID


CALIBRATION_ATTACKS = (
    "jpeg_80",
    "jpeg_50",
    "gaussian_5",
    "gaussian_12",
    "blur_0.8",
    "blur_1.5",
    "resize_075",
    "resize_050",
    "crop_05",
    "crop_10",
    "rotate_3",
    "rotate_7",
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


def _clean_distribution_features(clean: np.ndarray, visual: np.ndarray) -> np.ndarray:
    centered = clean - clean.mean(axis=0)
    _, _, right = np.linalg.svd(centered, full_matrices=False)
    scores = centered @ right[:8].T
    return np.concatenate([visual, scores], axis=1)


def _session_auc(
    features: np.ndarray,
    selected: np.ndarray,
    seed: int,
    repeats: int = 5,
    maximum_per_class: int = 500,
) -> tuple[float, list[float]]:
    selected = np.unique(np.asarray(selected, dtype=int))
    remaining = np.setdiff1d(np.arange(len(features)), selected)
    count = min(maximum_per_class, len(selected), len(remaining))
    if count < 10:
        return float("nan"), []
    values: list[float] = []
    for repeat in range(repeats):
        rng = np.random.default_rng(seed + repeat)
        positive = rng.choice(selected, count, replace=False)
        negative = rng.choice(remaining, count, replace=False)
        chosen = np.concatenate([positive, negative])
        targets = np.concatenate([np.ones(count), np.zeros(count)])
        train, test = train_test_split(
            np.arange(len(chosen)),
            test_size=0.35,
            random_state=seed + repeat,
            stratify=targets,
        )
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=3000, class_weight="balanced"),
        )
        model.fit(features[chosen][train], targets[train])
        probabilities = model.predict_proba(features[chosen][test])[:, 1]
        values.append(float(roc_auc_score(targets[test], probabilities)))
    return float(np.mean(values)), values


def _decode_attack(
    protocol: NarcisProtocol,
    transmission,
    received_labels: np.ndarray,
    encryption_key: bytes,
    sequence: int,
    plaintext: bytes,
) -> tuple[bool, int, float]:
    intended = np.asarray(
        [protocol.cover_index.labels[path] for path in transmission.covers],
        dtype=int,
    )
    try:
        recovered_envelope, corrections = protocol.decode_labels(
            received_labels.tolist(),
            transmission.padding_bits,
            sequence=sequence,
        )
        nonce, ciphertext = recovered_envelope[:12], recovered_envelope[12:]
        associated = PAYLOAD_ID + sequence.to_bytes(8, "big")
        recovered = AESGCM(encryption_key).decrypt(
            nonce,
            ciphertext,
            associated,
        )
        success = recovered == plaintext
    except Exception:
        corrections = -1
        success = False
    return (
        bool(success),
        int(corrections),
        float(np.mean(received_labels == intended)),
    )


def run_cached_partition(
    *,
    dataset_name: str,
    seed: int,
    cache: Path,
    output: Path,
    clusters: int = 8,
    group_size: int = 5,
    rs_parity: int = 128,
    include_holdout: bool = False,
) -> dict:
    if clusters != 8 or group_size != 5 or rs_parity != 128:
        raise ValueError("the external-validation runner is frozen at K=8, group_size=5, RS128")

    clean = np.load(cache / "clean.npy")
    visual = np.load(cache / "visual_features.npy")
    identifiers = (cache / "identifiers.txt").read_text(encoding="utf-8").splitlines()
    if not (len(clean) == len(visual) == len(identifiers)):
        raise ValueError("cached clean embeddings, visual features, and identifiers must align")

    calibration = {
        name: np.load(cache / f"{name}.npy", mmap_mode="r")
        for name in CALIBRATION_ATTACKS
    }
    choice, candidate_frame = select_group_bank_projection(
        clean,
        calibration,
        visual,
        clusters=clusters,
        group_size=group_size,
        principal_components=16,
        random_directions=32,
        random_seed=20260828 + seed,
    )
    banks, bank_diagnostics = build_balanced_group_bank(
        choice.labels,
        choice.calibration_correct,
        label_count=clusters,
        group_size=group_size,
        seed=20260830 + seed,
        restarts=10,
        swap_steps=6000,
    )
    signatures = majority_failure_signatures(
        banks,
        choice.calibration_correct,
    )
    index = CoverIndex.build(identifiers, choice.labels)
    master_key, encryption_key, workload = benchmark_workload(dataset_name, seed)
    protocol = NarcisProtocol(
        index,
        clusters,
        master_key,
        repetition=group_size,
        fec="reed_solomon",
        rs_parity=rs_parity,
    )
    positions = {identifier: offset for offset, identifier in enumerate(identifiers)}
    calibration_labels = {
        name: choice.codebook.predict(embeddings)
        for name, embeddings in calibration.items()
    }
    clean15 = _clean_distribution_features(clean, visual)

    frequency = np.zeros(len(identifiers), dtype=int)
    sessions: list[dict] = []
    for message in workload:
        transmission = encode_group_bank(
            protocol,
            message.envelope,
            sequence=message.sequence,
            identifiers=identifiers,
            banks=banks,
            signatures=signatures,
        )
        selected = np.asarray(
            [positions[path] for path in transmission.covers],
            dtype=int,
        )
        frequency[selected] += 1
        attack_rows = {}
        all_success = True
        maximum_corrections = 0
        for attack_name, all_received in calibration_labels.items():
            received = np.asarray(all_received[selected], dtype=int)
            success, corrections, symbol_accuracy = _decode_attack(
                protocol,
                transmission,
                received,
                encryption_key,
                message.sequence,
                message.plaintext,
            )
            all_success &= success
            if corrections >= 0:
                maximum_corrections = max(maximum_corrections, corrections)
            attack_rows[attack_name] = {
                "success": success,
                "rs_corrections": corrections,
                "cover_label_accuracy": symbol_accuracy,
            }

        global_mean, global_repeats = _session_auc(
            visual,
            selected,
            seed * 100000 + message.sequence * 100 + 11,
        )
        clean15_mean, clean15_repeats = _session_auc(
            clean15,
            selected,
            seed * 100000 + message.sequence * 100 + 23,
        )
        sessions.append(
            {
                "sequence": message.sequence,
                "payload_bytes": message.payload_bytes,
                "covers": len(transmission.covers),
                "all_calibration_success": bool(all_success),
                "maximum_rs_corrections": int(maximum_corrections),
                "global7_auc_mean": global_mean,
                "global7_auc_repetitions": global_repeats,
                "clean15_auc_mean": clean15_mean,
                "clean15_auc_repetitions": clean15_repeats,
                "attacks": attack_rows,
            }
        )

    calibration_trials = len(sessions) * len(CALIBRATION_ATTACKS)
    calibration_successes = sum(
        int(row["success"])
        for session in sessions
        for row in session["attacks"].values()
    )
    result = {
        "dataset": dataset_name,
        "seed": seed,
        "protocol": {
            "clusters": clusters,
            "group_size": group_size,
            "rs_parity": rs_parity,
            "sequences": [0, 29],
            "benchmark_master_key_sha256": hashlib.sha256(master_key).hexdigest(),
            "projection_seed": 20260828 + seed,
            "group_bank_seed": 20260830 + seed,
            "group_bank_restarts": 10,
            "group_bank_swap_steps": 6000,
        },
        "projection": {
            "direction": choice.name,
            "family": choice.family,
            "stable_images": int(choice.stable.sum()),
            "stable_fraction": float(choice.stable.mean()),
            "max_unavoidable_bad_fraction": choice.max_unavoidable_bad_fraction,
            "sum_unavoidable_bad_fraction": choice.sum_unavoidable_bad_fraction,
        },
        "calibration": {
            "trials": calibration_trials,
            "successes": calibration_successes,
            "success_rate": calibration_successes / calibration_trials,
            "global7_session_auc_mean": float(np.mean([row["global7_auc_mean"] for row in sessions])),
            "clean15_session_auc_mean": float(np.mean([row["clean15_auc_mean"] for row in sessions])),
            "maximum_rs_corrections": int(max(row["maximum_rs_corrections"] for row in sessions)),
        },
        "cover_usage": {
            "unique_covers": int(np.count_nonzero(frequency)),
            "minimum_frequency": int(frequency.min()),
            "maximum_frequency": int(frequency.max()),
            "mean_frequency": float(frequency.mean()),
            "frequency_cv": float(frequency.std() / max(frequency.mean(), 1e-12)),
        },
        "bank_diagnostics": [
            {
                "label": diagnostic.label,
                "covers": diagnostic.covers,
                "groups": diagnostic.groups,
                "bad_groups_by_attack": dict(zip(CALIBRATION_ATTACKS, diagnostic.bad_groups_by_attack, strict=True)),
                "lower_bound_by_attack": dict(zip(CALIBRATION_ATTACKS, diagnostic.lower_bound_by_attack, strict=True)),
                "reaches_lower_bound": diagnostic.reaches_lower_bound,
            }
            for diagnostic in bank_diagnostics
        ],
        "sessions": sessions,
    }

    if include_holdout:
        holdout = {}
        missing = [name for name in HOLDOUT_ATTACKS if not (cache / f"{name}.npy").exists()]
        if missing:
            raise FileNotFoundError(", ".join(missing))
        holdout_labels = {
            name: choice.codebook.predict(np.load(cache / f"{name}.npy", mmap_mode="r"))
            for name in HOLDOUT_ATTACKS
        }
        rows = []
        for message in workload:
            transmission = encode_group_bank(
                protocol,
                message.envelope,
                sequence=message.sequence,
                identifiers=identifiers,
                banks=banks,
                signatures=signatures,
            )
            selected = np.asarray([positions[path] for path in transmission.covers], dtype=int)
            for attack_name, all_received in holdout_labels.items():
                success, corrections, accuracy = _decode_attack(
                    protocol,
                    transmission,
                    np.asarray(all_received[selected], dtype=int),
                    encryption_key,
                    message.sequence,
                    message.plaintext,
                )
                rows.append(
                    {
                        "sequence": message.sequence,
                        "payload_bytes": message.payload_bytes,
                        "attack": attack_name,
                        "success": success,
                        "rs_corrections": corrections,
                        "cover_label_accuracy": accuracy,
                    }
                )
        for attack_name in HOLDOUT_ATTACKS:
            selected_rows = [row for row in rows if row["attack"] == attack_name]
            holdout[attack_name] = {
                "trials": len(selected_rows),
                "successes": sum(int(row["success"]) for row in selected_rows),
                "success_rate": float(np.mean([row["success"] for row in selected_rows])),
                "mean_cover_label_accuracy": float(np.mean([row["cover_label_accuracy"] for row in selected_rows])),
                "minimum_cover_label_accuracy": float(np.min([row["cover_label_accuracy"] for row in selected_rows])),
                "maximum_rs_corrections": int(max(row["rs_corrections"] for row in selected_rows)),
            }
        result["holdout"] = {
            "trials": len(rows),
            "successes": sum(int(row["success"]) for row in rows),
            "success_rate": float(np.mean([row["success"] for row in rows])),
            "by_attack": holdout,
            "rows": rows,
        }

    output.mkdir(parents=True, exist_ok=True)
    (output / "projection_candidates.csv").write_text(
        candidate_frame.to_csv(index=False),
        encoding="utf-8",
    )
    np.save(output / "cover_frequency.npy", frequency)
    (output / "validation.json").write_text(
        json.dumps(result, indent=2, allow_nan=True),
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--holdout", action="store_true")
    args = parser.parse_args()
    result = run_cached_partition(
        dataset_name=args.dataset_name,
        seed=args.seed,
        cache=args.cache,
        output=args.output,
        include_holdout=args.holdout,
    )
    print(json.dumps({
        "dataset": result["dataset"],
        "seed": result["seed"],
        "projection": result["projection"],
        "calibration": result["calibration"],
        "cover_usage": result["cover_usage"],
        **({"holdout": {key:value for key,value in result["holdout"].items() if key != "rows"}} if "holdout" in result else {}),
    }, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
