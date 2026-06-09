from argparse import ArgumentParser
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from time import perf_counter
import json
import math
import os
import random
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from scipy.stats import t
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from narcis.attacks import attack_suite
from narcis.augment import ChannelAugment
from narcis.baselines import dct_descriptor, histogram_descriptor
from narcis.cifar import CifarPartition, deterministic_partitions
from narcis.coding import encode_payload
from narcis.config import ModelConfig, TrainingConfig
from narcis.index import CoverIndex, NeuralCodebook, QuantileCodebook
from narcis.model import RobustImageEncoder
from narcis.protocol import NarcisProtocol
from narcis.security import decrypt_payload, encrypt_payload
from narcis.training import representation_loss


DESCRIPTORS = ("narcis_neural", "dct_16x16", "gray_histogram_64")
CLUSTER_CANDIDATES = (64, 32, 16, 8)
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


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_partition(dataset: CifarPartition, batch_size: int = 128):
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    images = []
    identifiers: list[str] = []
    for batch, names in loader:
        images.append(batch)
        identifiers.extend(names)
    return torch.cat(images), identifiers


def train_neural(
    dataset: CifarPartition,
    seed: int,
    epochs: int,
    output: Path,
    image_size: int,
) -> tuple[RobustImageEncoder, list[dict]]:
    seed_everything(seed)
    model = RobustImageEncoder(embedding_dim=64, base_channels=16)
    checkpoint = output / f"encoder_seed_{seed}.pt"
    if epochs == 0:
        model.load_state_dict(
            torch.load(checkpoint, map_location="cpu", weights_only=True)
        )
        return model.eval(), []
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)
    config = replace(
        TrainingConfig(),
        epochs=epochs,
        batch_size=64,
        seed=seed,
    )
    augment = ChannelAugment(image_size, seed)
    loader = DataLoader(
        dataset,
        batch_size=config.batch_size,
        shuffle=True,
        drop_last=True,
    )
    history = []
    for epoch in range(epochs):
        model.train()
        totals = Counter()
        batches = 0
        for images, _ in loader:
            first = torch.stack([augment(image) for image in images])
            second = torch.stack([augment(image) for image in images])
            optimizer.zero_grad(set_to_none=True)
            loss, metrics = representation_loss(model(first), model(second), config)
            loss.backward()
            optimizer.step()
            batches += 1
            totals.update(metrics)
        history.append(
            {
                "epoch": epoch + 1,
                **{
                    key: value / max(1, batches)
                    for key, value in totals.items()
                },
            }
        )
    output.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint)
    return model.eval(), history


@torch.no_grad()
def describe(
    name: str,
    images: torch.Tensor,
    model: RobustImageEncoder,
    batch_size: int = 128,
) -> np.ndarray:
    chunks = []
    for start in range(0, len(images), batch_size):
        batch = images[start : start + batch_size]
        if name == "narcis_neural":
            chunks.append(model(batch).cpu().numpy())
        elif name == "dct_16x16":
            chunks.append(dct_descriptor(batch))
        elif name == "gray_histogram_64":
            chunks.append(histogram_descriptor(batch))
        else:
            raise ValueError(name)
    return np.concatenate(chunks)


def attack_images(images: torch.Tensor, attack) -> torch.Tensor:
    return torch.stack([attack(image) for image in images])


def stable_index(
    descriptor_name: str,
    images: torch.Tensor,
    identifiers: list[str],
    model: RobustImageEncoder,
    clusters: int,
    seed: int,
    image_size: int,
) -> tuple[QuantileCodebook, CoverIndex, np.ndarray, np.ndarray]:
    clean_embeddings = describe(descriptor_name, images, model)
    codebook = QuantileCodebook.fit(clean_embeddings, clusters)
    clean_labels = codebook.predict(clean_embeddings)
    stable = np.ones(len(images), dtype=bool)
    suite = attack_suite(image_size, seed)
    for name in CALIBRATION_ATTACKS:
        attacked = attack_images(images, suite[name])
        labels = codebook.predict(describe(descriptor_name, attacked, model))
        stable &= labels == clean_labels
    stable_positions = np.flatnonzero(stable)
    visual_features = image_statistics(images)
    stability_target = stable.astype(int)
    propensity = LogisticRegression(max_iter=1000).fit(
        visual_features, stability_target
    ).predict_proba(visual_features)[:, 1]
    weights = np.clip(
        (1.0 - propensity) / np.maximum(propensity, 1e-4),
        0.05,
        20.0,
    )
    rng = np.random.default_rng(seed + clusters)
    priorities = -np.log(
        np.maximum(rng.random(len(images)), 1e-12)
    ) / weights
    stable_positions = sorted(
        stable_positions,
        key=lambda position: (
            int(clean_labels[position]),
            float(priorities[position]),
        ),
    )
    stable_paths = [identifiers[position] for position in stable_positions]
    stable_labels = clean_labels[stable_positions]
    index = CoverIndex.build(stable_paths, stable_labels)
    return codebook, index, clean_labels, stable


def encrypted_messages(seed: int, count: int, payload_bytes: int):
    rng = np.random.default_rng(seed)
    key = rng.bytes(32)
    messages = []
    for sequence in range(count):
        plaintext = rng.bytes(payload_bytes)
        encrypted = encrypt_payload(
            plaintext, key, sequence, nonce=rng.bytes(12)
        )
        messages.append((sequence, plaintext, encrypted))
    return key, messages


def choose_configuration(
    descriptor_name: str,
    images: torch.Tensor,
    identifiers: list[str],
    model: RobustImageEncoder,
    seed: int,
    image_size: int,
    messages,
    repetition: int,
    fec: str,
    rs_parity: int,
):
    trials = []
    for clusters in CLUSTER_CANDIDATES:
        codebook, index, clean_labels, stable = stable_index(
            descriptor_name,
            images,
            identifiers,
            model,
            clusters,
            seed,
            image_size,
        )
        protocol = NarcisProtocol(
            index,
            clusters,
            f"{descriptor_name}-{seed}".encode(),
            repetition=repetition,
            fec=fec,
            rs_parity=rs_parity,
        )
        feasible = all(protocol.feasibility(encrypted)[0] for _, _, encrypted in messages)
        counts = [len(index.buckets.get(label, [])) for label in range(clusters)]
        trial = {
            "clusters": clusters,
            "bits_per_cover": int(math.log2(clusters)),
            "stable_images": int(stable.sum()),
            "stable_fraction": float(stable.mean()),
            "minimum_bucket": min(counts),
            "maximum_bucket": max(counts),
            "occupancy_cv": float(np.std(counts) / max(np.mean(counts), 1e-12)),
            "feasible": feasible,
        }
        trials.append(trial)
        if feasible:
            return codebook, index, clean_labels, stable, protocol, trials
    raise RuntimeError(f"No feasible codebook for {descriptor_name}")


def end_to_end_attacks(
    descriptor_name: str,
    images: torch.Tensor,
    identifiers: list[str],
    model: RobustImageEncoder,
    codebook: QuantileCodebook,
    index: CoverIndex,
    protocol: NarcisProtocol,
    messages,
    payload_key: bytes,
    image_size: int,
    seed: int,
) -> tuple[list[dict], list[str]]:
    image_by_id = {
        identifier: images[position]
        for position, identifier in enumerate(identifiers)
    }
    rows = []
    all_selected: list[str] = []
    for sequence, plaintext, encrypted in messages:
        transmission = protocol.encode(encrypted)
        all_selected.extend(transmission.covers)
        selected = torch.stack([image_by_id[path] for path in transmission.covers])
        clean_labels = np.array([index.labels[path] for path in transmission.covers])
        for attack_name, attack in attack_suite(image_size, seed + sequence).items():
            attacked = attack_images(selected, attack)
            received = codebook.predict(describe(descriptor_name, attacked, model))
            symbol_accuracy = float(np.mean(received == clean_labels))
            try:
                recovered_encrypted, corrections = protocol.decode_labels(
                    received.tolist(), transmission.padding_bits
                )
                recovered = decrypt_payload(
                    recovered_encrypted, payload_key, sequence
                )
                success = recovered == plaintext
            except Exception:
                corrections = -1
                success = False
            rows.append(
                {
                    "descriptor": descriptor_name,
                    "sequence": sequence,
                    "attack": attack_name,
                    "covers": len(transmission.covers),
                    "symbol_accuracy": symbol_accuracy,
                    "message_success": int(success),
                    "hamming_corrections": corrections,
                }
            )
    return rows, all_selected


def image_statistics(images: torch.Tensor) -> np.ndarray:
    array = images.squeeze(1).numpy()
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
    return np.asarray(rows)


def steganalysis_auc(
    images: torch.Tensor,
    identifiers: list[str],
    selected_ids: list[str],
    seed: int,
) -> float:
    positions = {name: index for index, name in enumerate(identifiers)}
    selected_unique = list(dict.fromkeys(selected_ids))
    selected_indices = [positions[name] for name in selected_unique]
    rng = np.random.default_rng(seed)
    remaining = np.setdiff1d(np.arange(len(images)), selected_indices)
    count = min(len(selected_indices), len(remaining))
    if count < 20:
        return float("nan")
    positive = rng.choice(selected_indices, count, replace=False)
    negative = rng.choice(remaining, count, replace=False)
    x = image_statistics(torch.cat([images[positive], images[negative]]))
    y = np.concatenate([np.ones(count), np.zeros(count)])
    folds = StratifiedKFold(5, shuffle=True, random_state=seed)
    probabilities = cross_val_predict(
        LogisticRegression(max_iter=1000),
        x,
        y,
        cv=folds,
        method="predict_proba",
    )[:, 1]
    return float(roc_auc_score(y, probabilities))


def requested_symbol_entropy(protocol: NarcisProtocol, messages) -> float:
    counts = Counter()
    for _, _, encrypted in messages:
        required, _ = protocol.demand(encrypted)
        for cluster, count in required.items():
            counts[cluster] += count
    values = np.asarray(
        [counts.get(label, 0) for label in range(protocol.codebook_size)],
        dtype=float,
    )
    probabilities = values / max(values.sum(), 1.0)
    return float(
        -np.sum(probabilities * np.log2(probabilities + 1e-12))
    )


def scalability_rows(
    descriptor_name: str,
    embeddings: np.ndarray,
    seed: int,
) -> list[dict]:
    rows = []
    for size in (1000, 2500, 5000, 10000, len(embeddings)):
        if size > len(embeddings):
            continue
        sample = embeddings[:size]
        started = perf_counter()
        KMeans(n_clusters=64, random_state=seed, n_init=5).fit(sample)
        rows.append(
            {
                "descriptor": descriptor_name,
                "images": size,
                "kmeans_seconds": perf_counter() - started,
                "embedding_bytes": int(sample.nbytes),
            }
        )
    return rows


def confidence_interval(values: list[float]) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    mean = float(array.mean())
    if len(array) < 2:
        return mean, mean, mean
    half = float(t.ppf(0.975, len(array) - 1) * array.std(ddof=1) / np.sqrt(len(array)))
    return mean, mean - half, mean + half


def summarize(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = raw.groupby(["descriptor", "attack"])
    for (descriptor, attack), frame in grouped:
        message_values = frame.groupby("seed")["message_success"].mean().tolist()
        symbol_values = frame.groupby("seed")["symbol_accuracy"].mean().tolist()
        msg_mean, msg_low, msg_high = confidence_interval(message_values)
        sym_mean, sym_low, sym_high = confidence_interval(symbol_values)
        rows.append(
            {
                "descriptor": descriptor,
                "attack": attack,
                "message_success_mean": msg_mean,
                "message_success_ci95_low": msg_low,
                "message_success_ci95_high": msg_high,
                "symbol_accuracy_mean": sym_mean,
                "symbol_accuracy_ci95_low": sym_low,
                "symbol_accuracy_ci95_high": sym_high,
            }
        )
    return pd.DataFrame(rows)


def make_figures(summary: pd.DataFrame, scalability: pd.DataFrame, output: Path):
    attacks = [attack for attack in summary["attack"].unique() if attack != "clean"]
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(attacks))
    width = 0.25
    for offset, descriptor in enumerate(DESCRIPTORS):
        frame = summary[summary["descriptor"] == descriptor].set_index("attack")
        if frame.empty:
            continue
        values = [
            frame.loc[attack, "message_success_mean"]
            if attack in frame.index
            else 0.0
            for attack in attacks
        ]
        ax.bar(x + (offset - 1) * width, values, width, label=descriptor)
    ax.set_xticks(x, attacks, rotation=45, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Complete-message success rate")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / "message_success_by_attack.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    for descriptor, frame in scalability.groupby("descriptor"):
        ax.plot(
            frame["images"],
            frame["kmeans_seconds"],
            marker="o",
            label=descriptor,
        )
    ax.set_xlabel("Indexed images")
    ax.set_ylabel("K-means construction time (s)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output / "scalability.png", dpi=200)
    plt.close(fig)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=Path("dataset_external"))
    parser.add_argument("--output", type=Path, default=Path("experimental_results"))
    parser.add_argument("--seeds", default="11,29,47")
    parser.add_argument("--train-count", type=int, default=3000)
    parser.add_argument("--index-count", type=int, default=12000)
    parser.add_argument("--test-count", type=int, default=1000)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--messages", type=int, default=5)
    parser.add_argument("--payload-bytes", type=int, default=8)
    parser.add_argument("--repetition", type=int, default=3)
    parser.add_argument(
        "--fec",
        choices=("hamming", "reed_solomon"),
        default="hamming",
    )
    parser.add_argument("--rs-parity", type=int, default=64)
    parser.add_argument("--image-size", type=int, default=64)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    seeds = [int(value) for value in args.seeds.split(",")]

    attack_rows = []
    configuration_rows = []
    security_rows = []
    scale_rows = []
    training_rows = []
    ablation_rows = []

    for seed in seeds:
        train_indices, index_indices, _ = deterministic_partitions(
            seed, args.train_count, args.index_count, args.test_count
        )
        train_set = CifarPartition(
            args.dataset_root, True, train_indices, args.image_size
        )
        index_set = CifarPartition(
            args.dataset_root, True, index_indices, args.image_size
        )
        model, history = train_neural(
            train_set, seed, args.epochs, args.output, args.image_size
        )
        for row in history:
            training_rows.append({"seed": seed, **row})
        index_images, identifiers = load_partition(index_set)
        payload_key, messages = encrypted_messages(
            seed, args.messages, args.payload_bytes
        )

        for descriptor_name in DESCRIPTORS:
            try:
                (
                    codebook,
                    index,
                    _,
                    stable,
                    protocol,
                    trials,
                ) = choose_configuration(
                    descriptor_name,
                    index_images,
                    identifiers,
                    model,
                    seed,
                    args.image_size,
                    messages,
                    args.repetition,
                    args.fec,
                    args.rs_parity,
                )
            except RuntimeError:
                configuration_rows.append(
                    {
                        "seed": seed,
                        "descriptor": descriptor_name,
                        "clusters": 0,
                        "bits_per_cover": 0,
                        "stable_images": 0,
                        "stable_fraction": 0.0,
                        "minimum_bucket": 0,
                        "maximum_bucket": 0,
                        "occupancy_cv": float("nan"),
                        "feasible": False,
                    }
                )
                continue
            selected_trial = next(trial for trial in trials if trial["feasible"])
            configuration_rows.append(
                {
                    "seed": seed,
                    "descriptor": descriptor_name,
                    **selected_trial,
                }
            )
            rows, selected = end_to_end_attacks(
                descriptor_name,
                index_images,
                identifiers,
                model,
                codebook,
                index,
                protocol,
                messages,
                payload_key,
                args.image_size,
                seed,
            )
            attack_rows.extend({"seed": seed, **row} for row in rows)
            security_rows.append(
                {
                    "seed": seed,
                    "descriptor": descriptor_name,
                    "selection_steganalysis_auc": steganalysis_auc(
                        index_images, identifiers, selected, seed
                    ),
                    "stable_fraction": float(stable.mean()),
                    "encrypted_symbol_entropy_bits": requested_symbol_entropy(
                        protocol, messages
                    ),
                    "maximum_symbol_entropy_bits": float(
                        math.log2(protocol.codebook_size)
                    ),
                }
            )
            if descriptor_name == "narcis_neural":
                clean_embeddings = describe(
                    descriptor_name, index_images, model
                )
                clean_labels = codebook.predict(clean_embeddings)
                all_index = CoverIndex.build(identifiers, clean_labels)
                ablations = (
                    ("full", index, args.repetition),
                    ("no_stability_filter", all_index, args.repetition),
                    ("no_symbol_repetition", index, 1),
                )
                for ablation_name, ablation_index, repetition in ablations:
                    ablation_protocol = NarcisProtocol(
                        ablation_index,
                        protocol.codebook_size,
                        f"ablation-{seed}".encode(),
                        repetition=repetition,
                        fec=args.fec,
                        rs_parity=args.rs_parity,
                    )
                    if not all(
                        ablation_protocol.feasibility(encrypted)[0]
                        for _, _, encrypted in messages[:2]
                    ):
                        continue
                    ablation_attack_rows, _ = end_to_end_attacks(
                        descriptor_name,
                        index_images,
                        identifiers,
                        model,
                        codebook,
                        ablation_index,
                        ablation_protocol,
                        messages[:2],
                        payload_key,
                        args.image_size,
                        seed,
                    )
                    for row in ablation_attack_rows:
                        ablation_rows.append(
                            {
                                "seed": seed,
                                "ablation": ablation_name,
                                **row,
                            }
                        )
            embeddings = describe(descriptor_name, index_images, model)
            scale_rows.extend(
                {"seed": seed, **row}
                for row in scalability_rows(
                    descriptor_name, embeddings, seed
                )
            )

    raw = pd.DataFrame(attack_rows)
    configurations = pd.DataFrame(configuration_rows)
    security = pd.DataFrame(security_rows)
    scalability = pd.DataFrame(scale_rows)
    training = pd.DataFrame(training_rows)
    ablations = pd.DataFrame(ablation_rows)
    summary = summarize(raw)

    raw.to_csv(args.output / "end_to_end_raw.csv", index=False)
    summary.to_csv(args.output / "end_to_end_summary.csv", index=False)
    configurations.to_csv(args.output / "codebook_configurations.csv", index=False)
    security.to_csv(args.output / "security_analysis.csv", index=False)
    scalability.to_csv(args.output / "scalability_raw.csv", index=False)
    training.to_csv(args.output / "training_history.csv", index=False)
    ablations.to_csv(args.output / "ablation_raw.csv", index=False)
    make_figures(summary, scalability, args.output)

    neural = summary[summary["descriptor"] == "narcis_neural"]
    baseline = summary[summary["descriptor"] != "narcis_neural"]
    merged = neural.merge(
        baseline,
        on="attack",
        suffixes=("_neural", "_baseline"),
    )
    superiority = {
        descriptor: bool(
            (
                merged[merged["descriptor_baseline"] == descriptor][
                    "message_success_mean_neural"
                ]
                >= merged[merged["descriptor_baseline"] == descriptor][
                    "message_success_mean_baseline"
                ]
            ).all()
        )
        for descriptor in baseline["descriptor"].unique()
    }
    for descriptor in DESCRIPTORS[1:]:
        if descriptor not in superiority:
            superiority[descriptor] = bool(
                (
                    configurations[
                        configurations["descriptor"] == descriptor
                    ]["feasible"]
                    .astype(str)
                    .str.lower()
                    .eq("false")
                    .all()
                )
            )
    report = {
        "configuration": vars(args) | {"seeds": seeds},
        "matched_protocol_baseline_outcome": {
            descriptor: {
                "narcis_not_worse_on_all_common_attacks_or_baseline_infeasible": result,
                "scope": "local implementation, common qualification and dataset only",
            }
            for descriptor, result in superiority.items()
        },
        "published_sota_context": {
            "Guo_and_Ping_2026": {
                "reported_average_robustness": {
                    "Holidays_10_bits": 0.9954,
                    "VOC_14_bits": 0.9864,
                    "ImageNet_15_bits": 0.9719,
                },
                "doi": "10.1016/j.knosys.2026.115472",
                "cross_dataset_direct_superiority_claim_allowed": False,
            }
        },
        "security_mechanisms": {
            "payload": "AES-GCM with sequence-bound associated data",
            "metadata": "AES-GCM with sender/receiver associated data",
            "replay": "monotonic per-sender sequence guard",
            "error_control": (
                f"Reed-Solomon with {args.rs_parity} parity bytes"
                if args.fec == "reed_solomon"
                else f"Hamming(7,4) plus repetition-{args.repetition}"
            ),
            "fec_mode": args.fec,
            "reed_solomon_parity_bytes": args.rs_parity,
        },
    }
    serializable = json.loads(
        json.dumps(report, default=lambda value: str(value))
    )
    (args.output / "campaign_report.json").write_text(
        json.dumps(serializable, indent=2), encoding="utf-8"
    )
    print(json.dumps(serializable, indent=2))


if __name__ == "__main__":
    main()
