from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import csv
import hashlib
import json
import os
import platform
import sys

import numpy as np
import pandas as pd
import sklearn
import torch
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from narcis.attacks import attack_suite
from narcis.benchmark import benchmark_workload
from narcis.data import discover_images
from narcis.glcm import glcm_texture_features
from narcis.group_bank import build_balanced_group_bank
from narcis.group_bank_projection import select_group_bank_projection
from narcis.group_bank_protocol import encode_group_bank, majority_failure_signatures
from narcis.index import CoverIndex
from narcis.protocol import NarcisProtocol
from run_bossbase_campaign import (
    CALIBRATION_ATTACKS,
    NativeImageDataset,
    dataset_statistics,
    embed_dataset,
    model_view,
    residual_features,
    seed_everything,
    train_encoder,
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
    identifiers = []
    for path in paths:
        identifiers.append(path.resolve().relative_to(root).as_posix())
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("canonical identifiers are not unique")
    return identifiers


def make_schedule(
    *,
    dataset_root: Path,
    checkpoint_root: Path,
    output: Path,
    seed: int,
    epochs: int,
) -> tuple[NativeImageDataset, np.ndarray, list[str], dict, pd.DataFrame, list]:
    paths = discover_images(dataset_root)
    if len(paths) < 8500:
        raise ValueError(f"Caltech-101 requires >=8500 images, found {len(paths)}")

    order = np.random.default_rng(seed).permutation(len(paths))
    train_paths = [paths[position] for position in order[:1500]]
    index_paths = [paths[position] for position in order[1500:8500]]
    dataset = NativeImageDataset(index_paths, "RGB", 256)
    identifiers = canonical_identifiers(index_paths, dataset_root)

    checkpoint_root.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    model, history = train_encoder(
        train_paths,
        seed,
        epochs,
        128,
        64,
        output,
        checkpoint_root=checkpoint_root,
        input_mode="RGB",
        channel_size=256,
    )
    checkpoint = checkpoint_root / f"encoder_seed_{seed}.pt"
    actual_checkpoint_sha = sha256_file(checkpoint)

    clean, _, clean_seconds = embed_dataset(model, dataset, 128)
    suite = attack_suite(256, seed)
    attacked = {}
    attack_seconds = {}
    for attack_name in CALIBRATION_ATTACKS:
        values, _, seconds = embed_dataset(
            model,
            dataset,
            128,
            suite[attack_name],
        )
        attacked[attack_name] = values
        attack_seconds[attack_name] = seconds
    visual = dataset_statistics(dataset)

    choice, candidates = select_group_bank_projection(
        clean,
        attacked,
        visual,
        clusters=8,
        group_size=5,
        principal_components=16,
        random_directions=32,
        random_seed=20260828 + seed,
    )
    banks, diagnostics = build_balanced_group_bank(
        choice.labels,
        choice.calibration_correct,
        label_count=8,
        group_size=5,
        seed=20260830 + seed,
        restarts=10,
        swap_steps=6000,
    )
    signatures = majority_failure_signatures(banks, choice.calibration_correct)
    index = CoverIndex.build(identifiers, choice.labels)
    master_key, _, workload = benchmark_workload("Caltech-101", seed)
    protocol = NarcisProtocol(
        index,
        8,
        master_key,
        repetition=5,
        fec="reed_solomon",
        rs_parity=128,
    )
    positions = {identifier: position for position, identifier in enumerate(identifiers)}
    target = np.zeros((len(identifiers), len(workload)), dtype=np.uint8)
    schedule_rows = []
    session_rows = []
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
        session_rows.append(
            {
                "sequence": message.sequence,
                "payload_bytes": message.payload_bytes,
                "covers": len(selected),
            }
        )
        for position in selected:
            schedule_rows.append(
                {
                    "image_index": int(position),
                    "image_id": identifiers[int(position)],
                    "sequence": int(message.sequence),
                    "payload_bytes": int(message.payload_bytes),
                }
            )

    pd.DataFrame(schedule_rows).to_csv(output / "schedule.csv", index=False)
    pd.DataFrame(session_rows).to_csv(output / "schedule_summary.csv", index=False)
    candidates.to_csv(output / "projection_candidates.csv", index=False)
    if history:
        pd.DataFrame(history).to_csv(output / "training_history.csv", index=False)
    np.save(output / "session_target.npy", target)

    manifest = {
        "dataset": "Caltech-101",
        "seed": seed,
        "source_images_discovered": len(paths),
        "training_images": 1500,
        "index_images": 7000,
        "canonical_identifier_rule": "path relative to dataset root, POSIX separators",
        "checkpoint": {
            "path": str(checkpoint),
            "expected_sha256": EXPECTED_CHECKPOINT_SHA256.get(seed),
            "actual_sha256": actual_checkpoint_sha,
            "matches_recorded_fresh_campaign": actual_checkpoint_sha
            == EXPECTED_CHECKPOINT_SHA256.get(seed),
        },
        "projection": {
            "name": choice.name,
            "family": choice.family,
            "stable_images": int(choice.stable.sum()),
            "stable_fraction": float(choice.stable.mean()),
            "max_unavoidable_bad_fraction": float(choice.max_unavoidable_bad_fraction),
            "sum_unavoidable_bad_fraction": float(choice.sum_unavoidable_bad_fraction),
        },
        "group_bank": {
            "all_labels_reach_lower_bound": bool(all(item.reaches_lower_bound for item in diagnostics)),
            "group_size": 5,
            "restarts": 10,
            "swap_steps": 6000,
        },
        "schedule": {
            "sessions": len(workload),
            "all_index_covers_used": bool(np.all(target.sum(axis=1) > 0)),
            "minimum_sessions_per_cover": int(target.sum(axis=1).min()),
            "maximum_sessions_per_cover": int(target.sum(axis=1).max()),
            "mean_sessions_per_cover": float(target.sum(axis=1).mean()),
            "total_cover_emissions": int(target.sum()),
        },
        "timing": {
            "clean_embedding_seconds": clean_seconds,
            "calibration_embedding_seconds": attack_seconds,
        },
    }
    return dataset, target, identifiers, manifest, candidates, workload


class MultiHeadSelectionCNN(nn.Module):
    def __init__(self, in_channels: int, heads: int):
        super().__init__()
        self.network = nn.Sequential(
            nn.Conv2d(in_channels, 16, 5, padding=2, bias=False),
            nn.BatchNorm2d(16),
            nn.Tanh(),
            nn.AvgPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.SiLU(),
            nn.AvgPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.SiLU(),
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(64, heads),
        )

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return self.network(images)


def detector_features(dataset: NativeImageDataset, output: Path) -> tuple[np.ndarray, np.ndarray, torch.Tensor]:
    residual_path = output / "srm52_features.npy"
    glcm_path = output / "glcm5_features.npy"
    cnn_path = output / "cnn64_images.pt"
    if residual_path.exists() and glcm_path.exists() and cnn_path.exists():
        return (
            np.load(residual_path),
            np.load(glcm_path),
            torch.load(cnn_path, map_location="cpu", weights_only=True),
        )

    residual_rows = []
    glcm_rows = []
    cnn_rows = []
    for position in range(len(dataset)):
        image, _ = dataset[position]
        residual_rows.append(residual_features(image.numpy()))
        glcm_rows.append(glcm_texture_features(image.numpy()))
        cnn_rows.append(
            F.interpolate(
                image.unsqueeze(0),
                size=(64, 64),
                mode="bilinear",
                align_corners=False,
                antialias=True,
            ).squeeze(0)
        )
        if (position + 1) % 500 == 0:
            print(f"detector features: {position + 1}/{len(dataset)}", flush=True)
    residual = np.asarray(residual_rows, dtype=np.float32)
    glcm = np.asarray(glcm_rows, dtype=np.float64)
    cnn = torch.stack(cnn_rows)
    np.save(residual_path, residual)
    np.save(glcm_path, glcm)
    torch.save(cnn, cnn_path)
    return residual, glcm, cnn


def safe_auc(target: np.ndarray, score: np.ndarray) -> float:
    if np.unique(target).size < 2:
        return float("nan")
    return float(roc_auc_score(target, score))


def forest_probabilities(model: ExtraTreesClassifier, values: np.ndarray) -> list[np.ndarray]:
    probabilities = model.predict_proba(values)
    if not isinstance(probabilities, list):
        probabilities = [probabilities]
    rows = []
    for head, matrix in enumerate(probabilities):
        classes = np.asarray(model.classes_[head])
        where = np.flatnonzero(classes == 1)
        if where.size == 0:
            rows.append(np.zeros(len(values), dtype=float))
        else:
            rows.append(matrix[:, int(where[0])])
    return rows


def cnn_probabilities(
    images: torch.Tensor,
    target: np.ndarray,
    train: np.ndarray,
    test: np.ndarray,
    split_seed: int,
) -> np.ndarray:
    seed_everything(split_seed)
    model = MultiHeadSelectionCNN(images.shape[1], target.shape[1])
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_function = nn.BCEWithLogitsLoss()
    loader = DataLoader(
        TensorDataset(images[train], torch.from_numpy(target[train]).float()),
        batch_size=32,
        shuffle=True,
    )
    for _ in range(8):
        model.train()
        for batch, labels in loader:
            optimizer.zero_grad(set_to_none=True)
            loss = loss_function(model(batch), labels)
            loss.backward()
            optimizer.step()
    model.eval()
    with torch.no_grad():
        return torch.sigmoid(model(images[test])).cpu().numpy()


def run_detectors(
    *,
    dataset: NativeImageDataset,
    target: np.ndarray,
    seed: int,
    output: Path,
    repeats: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    residual, glcm, cnn_images = detector_features(dataset, output)
    repetition_rows = []
    head_rows = []
    indices = np.arange(len(dataset))
    for repeat in range(repeats):
        split_seed = seed * 10000 + repeat
        train, test = train_test_split(
            indices,
            test_size=0.35,
            random_state=split_seed,
            shuffle=True,
        )
        print(f"seed={seed} repeat={repeat} train={len(train)} test={len(test)}", flush=True)

        forest = ExtraTreesClassifier(
            n_estimators=300,
            max_features="sqrt",
            class_weight="balanced",
            random_state=split_seed,
            n_jobs=-1,
        )
        forest.fit(residual[train], target[train])
        forest_scores = forest_probabilities(forest, residual[test])
        forest_auc = [safe_auc(target[test, head], forest_scores[head]) for head in range(target.shape[1])]

        glcm_auc = []
        for head in range(target.shape[1]):
            labels = target[:, head]
            classifier = make_pipeline(
                StandardScaler(),
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=split_seed,
                ),
            )
            classifier.fit(glcm[train], labels[train])
            score = classifier.predict_proba(glcm[test])[:, 1]
            glcm_auc.append(safe_auc(labels[test], score))

        cnn_score = cnn_probabilities(cnn_images, target, train, test, split_seed)
        cnn_auc = [safe_auc(target[test, head], cnn_score[:, head]) for head in range(target.shape[1])]

        detector_values = {
            "srm52_extratrees": forest_auc,
            "glcm5_logistic": glcm_auc,
            "cnn30head": cnn_auc,
        }
        for detector_name, values in detector_values.items():
            for head, value in enumerate(values):
                head_rows.append(
                    {
                        "dataset": "Caltech-101",
                        "partition_seed": seed,
                        "repeat": repeat,
                        "split_seed": split_seed,
                        "detector": detector_name,
                        "session": head,
                        "auc": value,
                        "train_positives": int(target[train, head].sum()),
                        "test_positives": int(target[test, head].sum()),
                        "train_images": len(train),
                        "test_images": len(test),
                    }
                )
        repetition_rows.append(
            {
                "dataset": "Caltech-101",
                "partition_seed": seed,
                "repeat": repeat,
                "split_seed": split_seed,
                "srm52_extratrees_macro_auc": float(np.nanmean(forest_auc)),
                "glcm5_logistic_macro_auc": float(np.nanmean(glcm_auc)),
                "cnn30head_macro_auc": float(np.nanmean(cnn_auc)),
                "valid_srm_heads": int(np.isfinite(forest_auc).sum()),
                "valid_glcm_heads": int(np.isfinite(glcm_auc).sum()),
                "valid_cnn_heads": int(np.isfinite(cnn_auc).sum()),
            }
        )
        pd.DataFrame(repetition_rows).to_csv(output / "detector_repetitions.partial.csv", index=False)
        pd.DataFrame(head_rows).to_csv(output / "detector_heads.partial.csv", index=False)

    repetitions = pd.DataFrame(repetition_rows)
    heads = pd.DataFrame(head_rows)
    repetitions.to_csv(output / "detector_repetitions.csv", index=False)
    heads.to_csv(output / "detector_heads.csv", index=False)
    return repetitions, heads


def summarize(repetitions: pd.DataFrame) -> dict:
    summary = {}
    for column in (
        "srm52_extratrees_macro_auc",
        "glcm5_logistic_macro_auc",
        "cnn30head_macro_auc",
    ):
        values = repetitions[column].to_numpy(dtype=float)
        summary[column] = {
            "mean": float(np.nanmean(values)),
            "std": float(np.nanstd(values, ddof=1)),
            "min": float(np.nanmin(values)),
            "max": float(np.nanmax(values)),
            "repeats": int(np.isfinite(values).sum()),
        }
    return summary


def main() -> None:
    parser = ArgumentParser(description="Final frozen multi-session detector audit for NARCIS/Caltech-101")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True, choices=tuple(EXPECTED_CHECKPOINT_SHA256))
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--repeats", type=int, default=20)
    args = parser.parse_args()

    dataset_root = args.dataset_root.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    dataset, target, identifiers, manifest, _, workload = make_schedule(
        dataset_root=dataset_root,
        checkpoint_root=args.checkpoint_root,
        output=args.output,
        seed=args.seed,
        epochs=args.epochs,
    )
    repetitions, heads = run_detectors(
        dataset=dataset,
        target=target,
        seed=args.seed,
        output=args.output,
        repeats=args.repeats,
    )
    manifest["detectors"] = summarize(repetitions)
    manifest["environment"] = {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "github_sha": os.environ.get("GITHUB_SHA"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
    }
    manifest["artifacts"] = {
        "schedule_csv_sha256": sha256_file(args.output / "schedule.csv"),
        "session_target_npy_sha256": sha256_file(args.output / "session_target.npy"),
        "detector_repetitions_csv_sha256": sha256_file(args.output / "detector_repetitions.csv"),
        "detector_heads_csv_sha256": sha256_file(args.output / "detector_heads.csv"),
    }
    (args.output / "audit_manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=True),
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, allow_nan=True), flush=True)


if __name__ == "__main__":
    main()
