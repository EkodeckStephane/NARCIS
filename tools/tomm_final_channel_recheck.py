from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from narcis.attacks import attack_suite
from narcis.benchmark import benchmark_workload
from narcis.data import discover_images
from narcis.group_bank import build_balanced_group_bank
from narcis.group_bank_projection import select_group_bank_projection
from narcis.group_bank_protocol import encode_group_bank, majority_failure_signatures
from narcis.index import CoverIndex
from narcis.protocol import NarcisProtocol
from narcis.security import PAYLOAD_ID
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
        recovered = AESGCM(encryption_key).decrypt(nonce, ciphertext, associated)
        success = recovered == plaintext
    except Exception:
        corrections = -1
        success = False
    return bool(success), int(corrections), float(np.mean(received_labels == intended))


def main() -> None:
    parser = ArgumentParser(description="Aligned final NARCIS Caltech-101 channel recheck")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True, choices=tuple(EXPECTED_CHECKPOINT_SHA256))
    parser.add_argument("--epochs", type=int, default=5)
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
    protocol = NarcisProtocol(
        index,
        8,
        master_key,
        repetition=5,
        fec="reed_solomon",
        rs_parity=128,
    )
    positions = {identifier: position for position, identifier in enumerate(identifiers)}
    predicted = {name: choice.codebook.predict(values) for name, values in attacked.items()}

    raw_rows = []
    schedule_rows = []
    target = np.zeros((len(identifiers), len(workload)), dtype=np.uint8)
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
        if len(np.unique(selected)) != len(selected):
            raise RuntimeError(f"cover reuse within session {message.sequence}")
        target[selected, message.sequence] = 1
        for position in selected:
            schedule_rows.append(
                {
                    "image_index": int(position),
                    "image_id": identifiers[int(position)],
                    "sequence": int(message.sequence),
                    "payload_bytes": int(message.payload_bytes),
                }
            )
        for attack_name in all_attack_names:
            success, corrections, accuracy = decode_attack(
                protocol,
                transmission,
                np.asarray(predicted[attack_name][selected], dtype=int),
                encryption_key,
                message.sequence,
                message.plaintext,
            )
            raw_rows.append(
                {
                    "dataset": "Caltech-101",
                    "partition_seed": args.seed,
                    "sequence": int(message.sequence),
                    "payload_bytes": int(message.payload_bytes),
                    "attack": attack_name,
                    "attack_family": "calibration" if attack_name in CALIBRATION_ATTACKS else "holdout",
                    "success": bool(success),
                    "rs_corrections": int(corrections),
                    "cover_label_accuracy": float(accuracy),
                    "covers": len(selected),
                }
            )

    schedule = pd.DataFrame(schedule_rows).sort_values(
        ["sequence", "image_index"], kind="stable"
    ).reset_index(drop=True)
    schedule_path = args.output / "schedule.csv"
    if schedule_path.exists():
        existing = pd.read_csv(schedule_path).sort_values(
            ["sequence", "image_index"], kind="stable"
        ).reset_index(drop=True)
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

    manifest = {
        "dataset": "Caltech-101",
        "partition_seed": args.seed,
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
        "channel": family_summary,
        "timing": {
            "clean_embedding_seconds": clean_seconds,
            "attack_embedding_seconds": attack_seconds,
        },
        "artifacts": {
            "schedule_csv_sha256": sha256_file(schedule_path),
            "session_target_npy_sha256": sha256_file(args.output / "session_target.npy"),
            "channel_recheck_raw_csv_sha256": sha256_file(args.output / "channel_recheck_raw.csv"),
            "channel_recheck_summary_csv_sha256": sha256_file(args.output / "channel_recheck_summary.csv"),
        },
    }
    (args.output / "channel_recheck_manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=True), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, allow_nan=True), flush=True)


if __name__ == "__main__":
    main()
