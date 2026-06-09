from argparse import ArgumentParser
from collections import Counter
from dataclasses import replace
from pathlib import Path
from time import perf_counter
import json
import math
import random
import sys

import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageOps
from scipy.ndimage import convolve
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset, TensorDataset

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from narcis.attacks import attack_suite
from narcis.augment import ChannelAugment
from narcis.config import TrainingConfig
from narcis.data import discover_images
from narcis.index import CoverIndex, QuantileCodebook
from narcis.model import RobustImageEncoder
from narcis.protocol import NarcisProtocol
from narcis.security import decrypt_payload, encrypt_payload
from narcis.training import representation_loss


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
CANDIDATES = (64, 32, 16, 8)


class NativeImageDataset(Dataset):
    def __init__(
        self,
        paths: list[Path],
        mode: str = "L",
        channel_size: int | None = None,
    ):
        self.paths = paths
        self.mode = mode
        self.channel_size = channel_size

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int):
        path = self.paths[index]
        image = Image.open(path).convert(self.mode)
        if self.channel_size is not None:
            image = ImageOps.fit(
                image,
                (self.channel_size, self.channel_size),
                method=Image.Resampling.BICUBIC,
            )
        array = np.asarray(image, dtype=np.float32) / 255.0
        if array.ndim == 2:
            array = array[None, :, :]
        else:
            array = np.transpose(array, (2, 0, 1))
        return torch.from_numpy(array), str(path)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def model_view(images: torch.Tensor, size: int) -> torch.Tensor:
    return F.interpolate(
        images,
        size=(size, size),
        mode="bicubic",
        align_corners=False,
        antialias=True,
    )


def train_encoder(
    paths: list[Path],
    seed: int,
    epochs: int,
    model_size: int,
    embedding_dim: int,
    output: Path,
    checkpoint_root: Path | None = None,
    invariance_weight: float = 25.0,
    variance_weight: float = 25.0,
    covariance_weight: float = 1.0,
    input_mode: str = "L",
    channel_size: int | None = None,
) -> tuple[RobustImageEncoder, list[dict]]:
    seed_everything(seed)
    model = RobustImageEncoder(
        embedding_dim=embedding_dim,
        base_channels=16,
        in_channels=3 if input_mode == "RGB" else 1,
    )
    checkpoint = (checkpoint_root or output) / f"encoder_seed_{seed}.pt"
    if epochs == 0:
        model.load_state_dict(
            torch.load(checkpoint, map_location="cpu", weights_only=True)
        )
        return model.eval(), []

    dataset = NativeImageDataset(paths, input_mode, channel_size)
    loader = DataLoader(dataset, batch_size=16, shuffle=True, drop_last=True)
    augment = ChannelAugment(model_size, seed)
    config = replace(
        TrainingConfig(),
        epochs=epochs,
        batch_size=16,
        seed=seed,
        invariance_weight=invariance_weight,
        variance_weight=variance_weight,
        covariance_weight=covariance_weight,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)
    history = []
    for epoch in range(epochs):
        model.train()
        totals = Counter()
        batches = 0
        for native, _ in loader:
            resized = model_view(native, model_size)
            first = torch.stack([augment(image) for image in resized])
            second = torch.stack([augment(image) for image in resized])
            optimizer.zero_grad(set_to_none=True)
            loss, metrics = representation_loss(model(first), model(second), config)
            loss.backward()
            optimizer.step()
            batches += 1
            totals.update(metrics)
        history.append(
            {
                "seed": seed,
                "epoch": epoch + 1,
                **{key: value / batches for key, value in totals.items()},
            }
        )
    output.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint)
    return model.eval(), history


@torch.no_grad()
def embed_dataset(
    model: RobustImageEncoder,
    dataset: Dataset,
    model_size: int,
    attack=None,
    batch_size: int = 16,
) -> tuple[np.ndarray, list[str], float]:
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    embeddings = []
    identifiers = []
    started = perf_counter()
    for images, names in loader:
        if attack is not None:
            images = torch.stack([attack(image) for image in images])
        embeddings.append(model(model_view(images, model_size)).cpu().numpy())
        identifiers.extend(names)
    return np.concatenate(embeddings), identifiers, perf_counter() - started


def native_statistics(images: torch.Tensor) -> np.ndarray:
    array = images.mean(dim=1).numpy()
    rows = []
    for image in array:
        gx = np.diff(image, axis=1)
        gy = np.diff(image, axis=0)
        histogram, _ = np.histogram(image, bins=32, range=(0, 1), density=True)
        probabilities = histogram / max(histogram.sum(), 1e-12)
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-12))
        rows.append(
            [
                image.mean(),
                image.std(),
                np.mean(np.abs(gx)),
                np.mean(np.abs(gy)),
                entropy,
                np.quantile(image, 0.1),
                np.quantile(image, 0.9),
            ]
        )
    return np.asarray(rows, dtype=np.float32)


def dataset_statistics(dataset: Dataset, batch_size: int = 16) -> np.ndarray:
    rows = []
    for images, _ in DataLoader(dataset, batch_size=batch_size, shuffle=False):
        rows.append(native_statistics(images))
    return np.concatenate(rows)


def build_qualified_index(
    codebook: QuantileCodebook,
    identifiers: list[str],
    clean_labels: np.ndarray,
    stable: np.ndarray,
    visual_features: np.ndarray,
    seed: int,
) -> CoverIndex:
    target = stable.astype(int)
    propensity = LogisticRegression(max_iter=1000).fit(
        visual_features, target
    ).predict_proba(visual_features)[:, 1]
    weights = np.clip(
        (1.0 - propensity) / np.maximum(propensity, 1e-4),
        0.05,
        20.0,
    )
    rng = np.random.default_rng(seed + codebook.size)
    priorities = -np.log(np.maximum(rng.random(len(stable)), 1e-12)) / weights
    positions = sorted(
        np.flatnonzero(stable),
        key=lambda position: (
            int(clean_labels[position]),
            float(priorities[position]),
        ),
    )
    return CoverIndex.build(
        [identifiers[position] for position in positions],
        clean_labels[positions],
    )


def encrypted_messages(seed: int, count: int, payload_bytes: int):
    rng = np.random.default_rng(seed)
    key = rng.bytes(32)
    messages = []
    for sequence in range(count):
        plaintext = rng.bytes(payload_bytes)
        ciphertext = encrypt_payload(
            plaintext,
            key,
            sequence,
            nonce=rng.bytes(12),
        )
        messages.append((sequence, plaintext, ciphertext))
    return key, messages


def residual_features(image: np.ndarray) -> np.ndarray:
    kernels = (
        np.array([[0, -1, 0], [-1, 4, -1], [0, -1, 0]], dtype=np.float32),
        np.array([[-1, 2, -1]], dtype=np.float32),
        np.array([[-1], [2], [-1]], dtype=np.float32),
        np.array([[1, -1], [-1, 1]], dtype=np.float32),
    )
    features = []
    if image.ndim == 3:
        image = image.mean(axis=0)
    scaled = image * 255.0
    for kernel in kernels:
        residual = convolve(scaled, kernel, mode="reflect")
        clipped = np.clip(np.round(residual), -4, 4)
        histogram, _ = np.histogram(
            clipped,
            bins=np.arange(-4.5, 5.5, 1),
            density=True,
        )
        features.extend(histogram.tolist())
        features.extend(
            [
                float(residual.mean()),
                float(residual.std()),
                float(np.mean(np.abs(residual))),
                float(np.quantile(np.abs(residual), 0.9)),
            ]
        )
    return np.asarray(features, dtype=np.float32)


class SelectionCNN(nn.Module):
    def __init__(self, in_channels: int):
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
            nn.Linear(64, 1),
        )

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return self.network(images).squeeze(1)


def cnn_selection_auc(
    images: torch.Tensor,
    labels: np.ndarray,
    train: np.ndarray,
    test: np.ndarray,
    seed: int,
    epochs: int,
) -> float:
    seed_everything(seed)
    model = SelectionCNN(images.shape[1])
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=1e-3,
        weight_decay=1e-4,
    )
    loss_function = nn.BCEWithLogitsLoss()
    train_loader = DataLoader(
        TensorDataset(
            images[train],
            torch.from_numpy(labels[train]).float(),
        ),
        batch_size=32,
        shuffle=True,
    )
    model.train()
    for _ in range(epochs):
        for batch, targets in train_loader:
            optimizer.zero_grad(set_to_none=True)
            loss = loss_function(model(batch), targets)
            loss.backward()
            optimizer.step()
    model.eval()
    with torch.no_grad():
        probabilities = torch.sigmoid(model(images[test])).numpy()
    return float(roc_auc_score(labels[test], probabilities))


def selection_auc(
    dataset: NativeImageDataset,
    identifiers: list[str],
    selected_ids: list[str],
    seed: int,
    maximum_per_class: int = 500,
    cnn_epochs: int = 8,
) -> dict:
    positions = {name: index for index, name in enumerate(identifiers)}
    selected = np.asarray(
        [positions[name] for name in dict.fromkeys(selected_ids)],
        dtype=int,
    )
    remaining = np.setdiff1d(np.arange(len(dataset)), selected)
    count = min(len(selected), len(remaining), maximum_per_class)
    rng = np.random.default_rng(seed)
    positive = rng.choice(selected, count, replace=False)
    negative = rng.choice(remaining, count, replace=False)
    chosen = np.concatenate([positive, negative])
    labels = np.concatenate([np.ones(count), np.zeros(count)])

    global_rows = []
    residual_rows = []
    detector_images = []
    for position in chosen:
        image, _ = dataset[int(position)]
        global_rows.append(native_statistics(image.unsqueeze(0))[0])
        residual_rows.append(residual_features(image.numpy()))
        detector_images.append(
            F.interpolate(
                image.unsqueeze(0),
                size=(64, 64),
                mode="bilinear",
                align_corners=False,
                antialias=True,
            ).squeeze(0)
        )
    global_x = np.asarray(global_rows)
    residual_x = np.asarray(residual_rows)
    cnn_x = torch.stack(detector_images)
    train, test = train_test_split(
        np.arange(len(chosen)),
        test_size=0.35,
        random_state=seed,
        stratify=labels,
    )
    logistic = LogisticRegression(max_iter=1000).fit(
        global_x[train], labels[train]
    )
    forest = ExtraTreesClassifier(
        n_estimators=300,
        max_features="sqrt",
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    ).fit(residual_x[train], labels[train])
    return {
        "detector_samples_per_class": count,
        "global_logistic_auc": float(
            roc_auc_score(labels[test], logistic.predict_proba(global_x[test])[:, 1])
        ),
        "srm_lite_extratrees_auc": float(
            roc_auc_score(labels[test], forest.predict_proba(residual_x[test])[:, 1])
        ),
        "selection_cnn_auc": cnn_selection_auc(
            cnn_x,
            labels,
            train,
            test,
            seed,
            cnn_epochs,
        ),
        "srm_lite_features": int(residual_x.shape[1]),
        "cnn_epochs": cnn_epochs,
    }


def run_seed(args, paths: list[Path], seed: int):
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(paths))
    train_paths = [paths[index] for index in order[: args.train_count]]
    index_paths = [
        paths[index]
        for index in order[args.train_count : args.train_count + args.index_count]
    ]
    dataset = NativeImageDataset(
        index_paths,
        args.input_mode,
        args.channel_size,
    )
    model, history = train_encoder(
        train_paths,
        seed,
        args.epochs,
        args.model_size,
        args.embedding_dim,
        args.output,
        args.checkpoint_root,
        args.invariance_weight,
        args.variance_weight,
        args.covariance_weight,
        args.input_mode,
        args.channel_size,
    )
    clean, identifiers, clean_seconds = embed_dataset(
        model, dataset, args.model_size
    )
    codebooks = {
        size: QuantileCodebook.fit(clean, size) for size in CANDIDATES
    }
    clean_labels = {
        size: codebook.predict(clean) for size, codebook in codebooks.items()
    }
    stable = {
        size: np.ones(len(dataset), dtype=bool) for size in codebooks
    }
    suite = attack_suite(args.channel_size, seed)
    calibration_seconds = {}
    for attack_name in CALIBRATION_ATTACKS:
        attacked, _, seconds = embed_dataset(
            model,
            dataset,
            args.model_size,
            suite[attack_name],
        )
        for size, codebook in codebooks.items():
            stable[size] &= codebook.predict(attacked) == clean_labels[size]
        calibration_seconds[attack_name] = seconds

    visual_features = dataset_statistics(dataset)
    payload_key, messages = encrypted_messages(
        seed, args.messages, args.payload_bytes
    )
    trials = []
    selected = None
    for size in CANDIDATES:
        index = build_qualified_index(
            codebooks[size],
            identifiers,
            clean_labels[size],
            stable[size],
            visual_features,
            seed,
        )
        protocol = NarcisProtocol(
            index,
            size,
            f"bossbase-{seed}".encode(),
            fec="reed_solomon",
            rs_parity=args.rs_parity,
        )
        counts = [len(index.buckets.get(label, [])) for label in range(size)]
        feasible = all(
            protocol.feasibility(ciphertext)[0]
            for _, _, ciphertext in messages
        )
        trial = {
            "seed": seed,
            "clusters": size,
            "bits_per_cover": int(math.log2(size)),
            "stable_images": int(stable[size].sum()),
            "stable_fraction": float(stable[size].mean()),
            "minimum_bucket": int(min(counts)),
            "median_bucket": float(np.median(counts)),
            "maximum_bucket": int(max(counts)),
            "feasible": feasible,
        }
        trials.append(trial)
        if selected is None and feasible:
            selected = (
                trial,
                index,
                protocol,
                codebooks[size],
            )
    if selected is None:
        (args.output / f"infeasible_seed_{seed}.json").write_text(
            json.dumps(trials, indent=2), encoding="utf-8"
        )
        raise RuntimeError(
            f"No feasible BOSSBase configuration for seed {seed}; "
            f"see infeasible_seed_{seed}.json"
        )

    selected_trial, index, protocol, codebook = selected
    positions = {name: offset for offset, name in enumerate(identifiers)}
    attack_rows = []
    selected_ids = []
    end_to_end_started = perf_counter()
    for sequence, plaintext, ciphertext in messages:
        transmission = protocol.encode(ciphertext)
        selected_ids.extend(transmission.covers)
        native = torch.stack(
            [dataset[positions[name]][0] for name in transmission.covers]
        )
        intended = np.asarray([index.labels[name] for name in transmission.covers])
        for attack_name, attack in suite.items():
            attacked = torch.stack([attack(image) for image in native])
            with torch.no_grad():
                embeddings = model(model_view(attacked, args.model_size)).numpy()
            received = codebook.predict(embeddings)
            try:
                recovered_ciphertext, corrections = protocol.decode_labels(
                    received.tolist(), transmission.padding_bits
                )
                recovered = decrypt_payload(
                    recovered_ciphertext, payload_key, sequence
                )
                success = recovered == plaintext
            except Exception:
                corrections = -1
                success = False
            attack_rows.append(
                {
                    "seed": seed,
                    "sequence": sequence,
                    "attack": attack_name,
                    "covers": len(transmission.covers),
                    "symbol_accuracy": float(np.mean(received == intended)),
                    "message_success": int(success),
                    "rs_corrections": corrections,
                }
            )
    end_to_end_seconds = perf_counter() - end_to_end_started
    detectability = selection_auc(
        dataset,
        identifiers,
        selected_ids,
        seed,
        args.detector_samples,
        args.detector_epochs,
    )
    return {
        "history": history,
        "trials": trials,
        "attacks": attack_rows,
        "security": {
            "seed": seed,
            **detectability,
        },
        "timing": {
            "seed": seed,
            "clean_embedding_seconds": clean_seconds,
            "clean_images_per_second": len(dataset) / clean_seconds,
            "calibration_seconds": calibration_seconds,
            "end_to_end_seconds": end_to_end_seconds,
            "selected_clusters": selected_trial["clusters"],
        },
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("bossbase_results"))
    parser.add_argument("--seeds", default="11,29,47,71,101")
    parser.add_argument("--train-count", type=int, default=2000)
    parser.add_argument("--index-count", type=int, default=8000)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--messages", type=int, default=10)
    parser.add_argument("--payload-bytes", type=int, default=8)
    parser.add_argument("--rs-parity", type=int, default=64)
    parser.add_argument("--model-size", type=int, default=128)
    parser.add_argument("--embedding-dim", type=int, default=64)
    parser.add_argument("--detector-samples", type=int, default=500)
    parser.add_argument("--detector-epochs", type=int, default=8)
    parser.add_argument("--dataset-name", default="BOSSBase 1.01")
    parser.add_argument("--input-mode", choices=("L", "RGB"), default="L")
    parser.add_argument("--channel-size", type=int, default=512)
    parser.add_argument("--checkpoint-root", type=Path)
    parser.add_argument("--invariance-weight", type=float, default=25.0)
    parser.add_argument("--variance-weight", type=float, default=25.0)
    parser.add_argument("--covariance-weight", type=float, default=1.0)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    paths = discover_images(args.dataset_root)
    if args.train_count + args.index_count > len(paths):
        raise ValueError("Training and index partitions exceed the dataset")

    manifest = {
        "dataset_root": str(args.dataset_root.resolve()),
        "images": len(paths),
        "dataset": args.dataset_name,
        "source_resolution": "variable" if args.input_mode == "RGB" else [512, 512],
        "channel_resolution": [args.channel_size, args.channel_size],
        "model_input_resolution": [args.model_size, args.model_size],
        "configuration": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in vars(args).items()
        },
    }
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    all_history = []
    all_trials = []
    all_attacks = []
    all_security = []
    all_timing = []
    for seed in [int(value) for value in args.seeds.split(",")]:
        result = run_seed(args, paths, seed)
        all_history.extend(result["history"])
        all_trials.extend(result["trials"])
        all_attacks.extend(result["attacks"])
        all_security.append(result["security"])
        all_timing.append(result["timing"])
        pd.DataFrame(all_history).to_csv(
            args.output / "training_history.csv", index=False
        )
        pd.DataFrame(all_trials).to_csv(
            args.output / "codebook_trials.csv", index=False
        )
        pd.DataFrame(all_attacks).to_csv(
            args.output / "end_to_end_raw.csv", index=False
        )
        pd.DataFrame(all_security).to_csv(
            args.output / "selection_detectors.csv", index=False
        )
        (args.output / "timing.json").write_text(
            json.dumps(all_timing, indent=2), encoding="utf-8"
        )

    summary = (
        pd.DataFrame(all_attacks)
        .groupby("attack", as_index=False)
        .agg(
            trials=("message_success", "size"),
            message_success=("message_success", "mean"),
            symbol_accuracy=("symbol_accuracy", "mean"),
            minimum_symbol_accuracy=("symbol_accuracy", "min"),
        )
    )
    summary.to_csv(args.output / "end_to_end_summary.csv", index=False)
    report = {
        **manifest,
        "total_trials": len(all_attacks),
        "successful_trials": int(
            pd.DataFrame(all_attacks)["message_success"].sum()
        ),
        "mean_symbol_accuracy": float(
            pd.DataFrame(all_attacks)["symbol_accuracy"].mean()
        ),
        "worst_symbol_accuracy": float(
            pd.DataFrame(all_attacks)["symbol_accuracy"].min()
        ),
    }
    (args.output / "campaign_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
