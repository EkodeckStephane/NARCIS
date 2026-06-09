from argparse import ArgumentParser
from collections import Counter
from dataclasses import replace
from pathlib import Path
import json
import random
import sys

import numpy as np
import pandas as pd
import torch
from torch.nn import functional as F
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from narcis.attacks import attack_suite
from narcis.augment import ChannelAugment
from narcis.config import TrainingConfig
from narcis.data import discover_images
from narcis.index import QuantileCodebook
from narcis.model import RobustImageEncoder
from narcis.training import representation_loss
from run_bossbase_campaign import NativeImageDataset, model_view


CALIBRATION = (
    "jpeg_50",
    "gaussian_12",
    "blur_1.5",
    "resize_050",
    "crop_10",
    "rotate_7",
)
CONFIGURATIONS = (
    {
        "name": "reference_64d_25_25_1",
        "embedding_dim": 64,
        "invariance_weight": 25.0,
        "variance_weight": 25.0,
        "covariance_weight": 1.0,
    },
    {
        "name": "dimension_32",
        "embedding_dim": 32,
        "invariance_weight": 25.0,
        "variance_weight": 25.0,
        "covariance_weight": 1.0,
    },
    {
        "name": "dimension_128",
        "embedding_dim": 128,
        "invariance_weight": 25.0,
        "variance_weight": 25.0,
        "covariance_weight": 1.0,
    },
    {
        "name": "equal_weights_1_1_1",
        "embedding_dim": 64,
        "invariance_weight": 1.0,
        "variance_weight": 1.0,
        "covariance_weight": 1.0,
    },
    {
        "name": "reduced_variance_25_10_1",
        "embedding_dim": 64,
        "invariance_weight": 25.0,
        "variance_weight": 10.0,
        "covariance_weight": 1.0,
    },
)


def train(paths, seed, model_size, epochs, configuration):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    model = RobustImageEncoder(
        embedding_dim=configuration["embedding_dim"],
        base_channels=16,
    )
    dataset = NativeImageDataset(paths)
    loader = DataLoader(dataset, batch_size=16, shuffle=True, drop_last=True)
    augment = ChannelAugment(model_size, seed)
    config = replace(
        TrainingConfig(),
        epochs=epochs,
        batch_size=16,
        seed=seed,
        invariance_weight=configuration["invariance_weight"],
        variance_weight=configuration["variance_weight"],
        covariance_weight=configuration["covariance_weight"],
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)
    history = []
    for epoch in range(epochs):
        totals = Counter()
        batches = 0
        model.train()
        for native, _ in loader:
            resized = model_view(native, model_size)
            first = torch.stack([augment(image) for image in resized])
            second = torch.stack([augment(image) for image in resized])
            optimizer.zero_grad(set_to_none=True)
            loss, metrics = representation_loss(model(first), model(second), config)
            loss.backward()
            optimizer.step()
            totals.update(metrics)
            batches += 1
        history.append(
            {
                "configuration": configuration["name"],
                "epoch": epoch + 1,
                **{key: value / batches for key, value in totals.items()},
            }
        )
    return model.eval(), history


@torch.no_grad()
def embed(model, dataset, model_size, attack=None):
    rows = []
    for native, _ in DataLoader(dataset, batch_size=16, shuffle=False):
        if attack is not None:
            native = torch.stack([attack(image) for image in native])
        rows.append(model(model_view(native, model_size)).numpy())
    return np.concatenate(rows)


def direction_metrics(clean, attacked_by_name, clusters):
    centered = clean - clean.mean(axis=0)
    _, singular, right = np.linalg.svd(centered, full_matrices=False)
    explained = singular**2 / np.sum(singular**2)
    rows = []
    directions = {
        "pc1": right[0],
        "pc2": right[1],
        "pc3": right[2],
    }
    rng = np.random.default_rng(20260609)
    random_direction = rng.normal(size=clean.shape[1])
    directions["random"] = random_direction / np.linalg.norm(random_direction)
    for name, direction in directions.items():
        projection = centered @ direction
        boundaries = np.quantile(
            projection, np.arange(1, clusters) / clusters
        )
        clean_labels = np.digitize(projection, boundaries)
        stable = np.ones(len(clean), dtype=bool)
        for attacked in attacked_by_name.values():
            attacked_projection = (attacked - clean.mean(axis=0)) @ direction
            stable &= np.digitize(attacked_projection, boundaries) == clean_labels
        counts = np.bincount(clean_labels[stable], minlength=clusters)
        rows.append(
            {
                "direction": name,
                "explained_variance": (
                    float(explained[int(name[-1]) - 1])
                    if name.startswith("pc")
                    else float("nan")
                ),
                "stable_fraction": float(stable.mean()),
                "minimum_bucket": int(counts.min()),
                "occupancy_cv": float(
                    counts.std() / max(counts.mean(), 1e-12)
                ),
            }
        )
    return rows, explained


def main():
    parser = ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("bossbase_sensitivity"))
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--train-count", type=int, default=500)
    parser.add_argument("--index-count", type=int, default=1500)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--model-size", type=int, default=96)
    parser.add_argument("--clusters", type=int, default=16)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    paths = discover_images(args.dataset_root)
    order = np.random.default_rng(args.seed).permutation(len(paths))
    train_paths = [paths[index] for index in order[: args.train_count]]
    index_paths = [
        paths[index]
        for index in order[args.train_count : args.train_count + args.index_count]
    ]
    dataset = NativeImageDataset(index_paths)
    suite = attack_suite(512, args.seed)

    summary_rows = []
    history_rows = []
    direction_rows = []
    spectra = []
    for configuration in CONFIGURATIONS:
        model, history = train(
            train_paths,
            args.seed,
            args.model_size,
            args.epochs,
            configuration,
        )
        history_rows.extend(history)
        clean = embed(model, dataset, args.model_size)
        codebook = QuantileCodebook.fit(clean, args.clusters)
        clean_labels = codebook.predict(clean)
        stable = np.ones(len(clean), dtype=bool)
        attacked_by_name = {}
        for attack_name in CALIBRATION:
            attacked = embed(model, dataset, args.model_size, suite[attack_name])
            attacked_by_name[attack_name] = attacked
            stable &= codebook.predict(attacked) == clean_labels
        counts = np.bincount(clean_labels[stable], minlength=args.clusters)
        summary_rows.append(
            {
                **configuration,
                "final_loss": history[-1]["loss"],
                "stable_fraction": float(stable.mean()),
                "minimum_bucket": int(counts.min()),
                "occupancy_cv": float(
                    counts.std() / max(counts.mean(), 1e-12)
                ),
            }
        )
        if configuration["name"] == "reference_64d_25_25_1":
            directions, explained = direction_metrics(
                clean, attacked_by_name, args.clusters
            )
            direction_rows.extend(directions)
            spectra.extend(
                {
                    "component": index + 1,
                    "explained_variance": float(value),
                    "cumulative_variance": float(explained[: index + 1].sum()),
                }
                for index, value in enumerate(explained)
            )

    pd.DataFrame(summary_rows).to_csv(
        args.output / "configuration_summary.csv", index=False
    )
    pd.DataFrame(history_rows).to_csv(
        args.output / "training_history.csv", index=False
    )
    pd.DataFrame(direction_rows).to_csv(
        args.output / "direction_summary.csv", index=False
    )
    pd.DataFrame(spectra).to_csv(
        args.output / "pca_spectrum.csv", index=False
    )
    report = {
        "dataset": "BOSSBase 1.01",
        "seed": args.seed,
        "train_images": args.train_count,
        "index_images": args.index_count,
        "epochs": args.epochs,
        "channel_resolution": [512, 512],
        "model_input_resolution": [args.model_size, args.model_size],
        "calibration_attacks": list(CALIBRATION),
        "scope": "targeted sensitivity analysis; not the principal campaign",
    }
    (args.output / "manifest.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
