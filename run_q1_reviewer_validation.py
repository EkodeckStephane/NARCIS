from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import json
import math
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from scipy.stats import spearmanr, t
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.nn import functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from narcis.attacks import attack_suite
from narcis.coding import encode_payload_rs
from narcis.data import discover_images
from narcis.index import CoverIndex, QuantileCodebook
from narcis.protocol import NarcisProtocol
from narcis.security import decrypt_payload, encrypt_payload
from run_bossbase_campaign import (
    CALIBRATION_ATTACKS,
    NativeImageDataset,
    build_qualified_index,
    cnn_selection_auc,
    dataset_statistics,
    embed_dataset,
    encrypted_messages,
    model_view,
    native_statistics,
    seed_everything,
    train_encoder,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "q1_reviewer_results"
FIGURES = ROOT / "paper" / "figures"
PAYLOAD_SIZES = (8, 32, 128)
PROJECTION_COMPONENTS = 16
RANDOM_DIRECTIONS = 32


def ci95(values: list[float]) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    mean = float(array.mean())
    if len(array) < 2:
        return mean, mean, mean
    half = float(
        t.ppf(0.975, len(array) - 1)
        * array.std(ddof=1)
        / math.sqrt(len(array))
    )
    return mean, mean - half, mean + half


def payload_scalability() -> None:
    rows = []
    key = bytes(range(32))
    nonce = bytes(range(12))
    for payload_bytes in PAYLOAD_SIZES:
        encrypted = encrypt_payload(
            bytes(payload_bytes), key, 0, nonce=nonce
        )
        coded_bytes = len(encode_payload_rs(encrypted, 128)) // 8
        framed_bytes = len(encrypted) + 10
        rs_blocks = math.ceil(framed_bytes / (255 - 128))
        for clusters in (8, 16):
            index = CoverIndex(
                {
                    label: [f"{label}-{offset}" for offset in range(5000)]
                    for label in range(clusters)
                },
                {},
            )
            protocol = NarcisProtocol(
                index,
                clusters,
                b"payload-scalability",
                fec="reed_solomon",
                rs_parity=128,
            )
            transmission = protocol.encode(encrypted)
            rows.append(
                {
                    "payload_bytes": payload_bytes,
                    "encrypted_bytes": len(encrypted),
                    "framing_bytes": 10,
                    "rs_parity_bytes_per_block": 128,
                    "rs_blocks": rs_blocks,
                    "effective_parity_bytes": coded_bytes - framed_bytes,
                    "coded_bytes": coded_bytes,
                    "clusters": clusters,
                    "bits_per_symbol": int(math.log2(clusters)),
                    "covers_required": len(transmission.covers),
                    "net_bits_per_cover": (
                        8 * payload_bytes / len(transmission.covers)
                    ),
                }
            )
    frame = pd.DataFrame(rows)
    frame.to_csv(OUTPUT / "payload_scalability.csv", index=False)
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    for clusters, group in frame.groupby("clusters"):
        ax.plot(
            group["payload_bytes"],
            group["net_bits_per_cover"],
            marker="o",
            linewidth=2,
            label=f"K={clusters}",
        )
    ax.set_xscale("log", base=2)
    ax.set_xticks(PAYLOAD_SIZES, [str(value) for value in PAYLOAD_SIZES])
    ax.set_xlabel("Plaintext payload (bytes)")
    ax.set_ylabel("Net plaintext bits per transmitted cover")
    ax.grid(alpha=0.25)
    ax.legend(title="Codebook")
    fig.tight_layout()
    fig.savefig(FIGURES / "Fig_03.pdf", bbox_inches="tight")
    fig.savefig(
        FIGURES / "Fig_03.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)


def summary_figures() -> None:
    targeted = pd.read_csv(OUTPUT / "boss_seed11_ablation_summary.csv")
    unqualified = targeted[
        targeted["variant"] == "pc1_no_qualification"
    ].copy()
    principal = pd.read_csv(
        ROOT / "bossbase_results_rs128_final" / "end_to_end_raw.csv"
    )
    principal = principal[principal["seed"] == 11]
    qualified = (
        principal.groupby("attack", as_index=False)
        .agg(
            trials=("message_success", "size"),
            successes=("message_success", "sum"),
            message_success=("message_success", "mean"),
            symbol_accuracy=("symbol_accuracy", "mean"),
            minimum_symbol_accuracy=("symbol_accuracy", "min"),
        )
    )
    qualified.insert(0, "variant", "pc1_qualified")
    ablation = pd.concat([unqualified, qualified], ignore_index=True)
    ablation.to_csv(
        OUTPUT / "boss_seed11_matched_ablation_summary.csv", index=False
    )

    candidates = pd.read_csv(OUTPUT / "boss_projection_candidates.csv")
    analysis = json.loads(
        (OUTPUT / "boss_projection_analysis.json").read_text(encoding="utf-8")
    )
    fig, ax = plt.subplots(figsize=(6.8, 4.4))
    for family, colour, label in (
        ("pca", "#315f8c", "Principal directions"),
        ("fixed_random", "#c58b2a", "Fixed random directions"),
    ):
        frame = candidates[candidates["family"] == family]
        ax.scatter(
            frame["stable_fraction"],
            frame["minimum_bucket"],
            alpha=0.75,
            s=34,
            color=colour,
            label=label,
        )
    for name, marker, colour in (
        ("pc1", "s", "#111111"),
        (analysis["selected_direction"], "*", "#b54a4a"),
    ):
        row = candidates[candidates["direction"] == name].iloc[0]
        ax.scatter(
            [row["stable_fraction"]],
            [row["minimum_bucket"]],
            s=130,
            marker=marker,
            color=colour,
            edgecolor="white",
            linewidth=0.8,
            zorder=4,
            label=name,
        )
    ax.set_xlabel("Fraction stable under all calibration attacks")
    ax.set_ylabel("Minimum stable bucket size")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "Fig_09.pdf", bbox_inches="tight")
    fig.savefig(
        FIGURES / "Fig_09.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)

    repetitions = pd.read_csv(
        OUTPUT / "caltech_seed47_cnn_repetitions.csv"
    )
    report = json.loads(
        (OUTPUT / "caltech_seed47_selection_report.json").read_text(
            encoding="utf-8"
        )
    )
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    ax.scatter(
        repetitions["repeat"] + 1,
        repetitions["cnn_auc"],
        color="#315f8c",
        s=38,
    )
    ax.axhline(0.5, color="black", linestyle="--", linewidth=1)
    ax.axhline(
        report["cnn_auc_mean"],
        color="#b54a4a",
        linewidth=2,
        label="mean",
    )
    ax.fill_between(
        [0.5, len(repetitions) + 0.5],
        report["cnn_auc_ci95_low"],
        report["cnn_auc_ci95_high"],
        color="#b54a4a",
        alpha=0.15,
        label="95% CI",
    )
    ax.set_xlim(0.5, len(repetitions) + 0.5)
    ax.set_xlabel("Independent split and CNN initialisation")
    ax.set_ylabel("Selection-detection AUC")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(
        FIGURES / "Fig_08.pdf",
        bbox_inches="tight",
    )
    fig.savefig(
        FIGURES / "Fig_08.png",
        dpi=300,
        bbox_inches="tight",
    )
    plt.close(fig)


def prepare_embeddings(
    dataset_root: Path,
    checkpoint_root: Path,
    dataset_name: str,
    seed: int,
    train_count: int,
    index_count: int,
    input_mode: str,
    channel_size: int,
) -> tuple[
    NativeImageDataset,
    torch.nn.Module,
    np.ndarray,
    list[str],
    dict[str, np.ndarray],
]:
    cache = OUTPUT / f"{dataset_name.lower()}_seed{seed}_embeddings.npz"
    paths = discover_images(dataset_root)
    order = np.random.default_rng(seed).permutation(len(paths))
    train_paths = [paths[index] for index in order[:train_count]]
    index_paths = [
        paths[index]
        for index in order[train_count : train_count + index_count]
    ]
    dataset = NativeImageDataset(index_paths, input_mode, channel_size)
    model, _ = train_encoder(
        train_paths,
        seed,
        0,
        128,
        64,
        OUTPUT,
        checkpoint_root=checkpoint_root,
        input_mode=input_mode,
        channel_size=channel_size,
    )
    if cache.exists():
        stored = np.load(cache)
        clean = stored["clean"]
        attacked = {
            name: stored[name] for name in CALIBRATION_ATTACKS
        }
        identifiers = [str(path) for path in index_paths]
        return dataset, model, clean, identifiers, attacked

    clean, identifiers, _ = embed_dataset(model, dataset, 128)
    suite = attack_suite(channel_size, seed)
    attacked = {}
    for name in CALIBRATION_ATTACKS:
        attacked[name], _, _ = embed_dataset(
            model, dataset, 128, suite[name]
        )
    np.savez_compressed(cache, clean=clean, **attacked)
    return dataset, model, clean, identifiers, attacked


def stability_metrics(
    codebook: QuantileCodebook,
    clean: np.ndarray,
    attacked: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    labels = codebook.predict(clean)
    stable = np.ones(len(clean), dtype=bool)
    for embeddings in attacked.values():
        stable &= codebook.predict(embeddings) == labels
    return labels, stable


def direction_candidates(clean: np.ndarray) -> tuple[list[dict], np.ndarray]:
    centered = clean - clean.mean(axis=0)
    _, singular, right = np.linalg.svd(centered, full_matrices=False)
    explained = singular**2 / np.sum(singular**2)
    rows = [
        {
            "name": f"pc{index + 1}",
            "family": "pca",
            "direction": right[index],
            "explained_variance": float(explained[index]),
        }
        for index in range(min(PROJECTION_COMPONENTS, len(right)))
    ]
    rng = np.random.default_rng(20260609)
    for index in range(RANDOM_DIRECTIONS):
        direction = rng.normal(size=clean.shape[1])
        direction /= np.linalg.norm(direction)
        rows.append(
            {
                "name": f"random_{index + 1:02d}",
                "family": "fixed_random",
                "direction": direction,
                "explained_variance": float("nan"),
            }
        )
    return rows, explained


def evaluate_projection_candidates(
    clean: np.ndarray,
    attacked: dict[str, np.ndarray],
    clusters: int,
) -> tuple[pd.DataFrame, dict]:
    candidates, _ = direction_candidates(clean)
    rows = []
    for candidate in candidates:
        codebook = QuantileCodebook.fit_direction(
            clean, clusters, candidate["direction"]
        )
        labels, stable = stability_metrics(codebook, clean, attacked)
        counts = np.bincount(labels[stable], minlength=clusters)
        rows.append(
            {
                "direction": candidate["name"],
                "family": candidate["family"],
                "explained_variance": candidate["explained_variance"],
                "stable_images": int(stable.sum()),
                "stable_fraction": float(stable.mean()),
                "minimum_bucket": int(counts.min()),
                "occupancy_cv": float(
                    counts.std() / max(counts.mean(), 1e-12)
                ),
            }
        )
    frame = pd.DataFrame(rows)
    selected = (
        frame.sort_values(
            ["minimum_bucket", "stable_images", "occupancy_cv", "direction"],
            ascending=[False, False, True, True],
        )
        .iloc[0]
        .to_dict()
    )
    return frame, selected


def end_to_end_variant(
    name: str,
    dataset: NativeImageDataset,
    model: torch.nn.Module,
    identifiers: list[str],
    codebook: QuantileCodebook,
    index: CoverIndex,
    seed: int,
    message_count: int = 10,
) -> list[dict]:
    key, messages = encrypted_messages(seed, message_count, 8)
    protocol = NarcisProtocol(
        index,
        codebook.size,
        f"bossbase-{seed}".encode(),
        fec="reed_solomon",
        rs_parity=128,
    )
    positions = {name: offset for offset, name in enumerate(identifiers)}
    suite = attack_suite(512, seed)
    rows = []
    for sequence, plaintext, encrypted in messages:
        transmission = protocol.encode(encrypted)
        native = torch.stack(
            [dataset[positions[path]][0] for path in transmission.covers]
        )
        intended = np.asarray(
            [index.labels[path] for path in transmission.covers]
        )
        for attack_name, attack in suite.items():
            damaged = torch.stack([attack(image) for image in native])
            with torch.no_grad():
                embeddings = model(model_view(damaged, 128)).numpy()
            received = codebook.predict(embeddings)
            try:
                recovered_encrypted, corrections = protocol.decode_labels(
                    received.tolist(), transmission.padding_bits
                )
                recovered = decrypt_payload(
                    recovered_encrypted, key, sequence
                )
                success = recovered == plaintext
            except Exception:
                corrections = -1
                success = False
            rows.append(
                {
                    "variant": name,
                    "seed": seed,
                    "sequence": sequence,
                    "attack": attack_name,
                    "covers": len(transmission.covers),
                    "symbol_accuracy": float(np.mean(received == intended)),
                    "message_success": int(success),
                    "rs_corrections": corrections,
                }
            )
    return rows


def bossbase_ablation_and_projection(dataset_root: Path) -> None:
    seed = 11
    dataset, model, clean, identifiers, attacked = prepare_embeddings(
        dataset_root,
        ROOT / "bossbase_results",
        "bossbase",
        seed,
        2000,
        8000,
        "L",
        512,
    )
    visual_features = dataset_statistics(dataset)
    candidates, _ = evaluate_projection_candidates(clean, attacked, 16)
    candidates.to_csv(OUTPUT / "boss_projection_candidates.csv", index=False)
    selected_row = (
        candidates.sort_values(
            ["minimum_bucket", "stable_images", "occupancy_cv", "direction"],
            ascending=[False, False, True, True],
        )
        .iloc[0]
    )
    candidate_definitions, _ = direction_candidates(clean)
    direction = next(
        row["direction"]
        for row in candidate_definitions
        if row["name"] == selected_row["direction"]
    )

    pc1 = QuantileCodebook.fit(clean, 16)
    pc1_labels, pc1_stable = stability_metrics(pc1, clean, attacked)
    unqualified = CoverIndex.build(identifiers, pc1_labels)

    selected_codebook = QuantileCodebook.fit_direction(clean, 16, direction)
    selected_labels, selected_stable = stability_metrics(
        selected_codebook, clean, attacked
    )
    selected_index = build_qualified_index(
        selected_codebook,
        identifiers,
        selected_labels,
        selected_stable,
        visual_features,
        seed,
    )

    rows = []
    rows.extend(
        end_to_end_variant(
            "pc1_no_qualification",
            dataset,
            model,
            identifiers,
            pc1,
            unqualified,
            seed,
        )
    )
    rows.extend(
        end_to_end_variant(
            "attack_aware_qualified",
            dataset,
            model,
            identifiers,
            selected_codebook,
            selected_index,
            seed,
        )
    )
    raw = pd.DataFrame(rows)
    raw.to_csv(OUTPUT / "boss_seed11_ablation_raw.csv", index=False)
    summary = (
        raw.groupby(["variant", "attack"], as_index=False)
        .agg(
            trials=("message_success", "size"),
            successes=("message_success", "sum"),
            message_success=("message_success", "mean"),
            symbol_accuracy=("symbol_accuracy", "mean"),
            minimum_symbol_accuracy=("symbol_accuracy", "min"),
        )
    )
    summary.to_csv(OUTPUT / "boss_seed11_ablation_summary.csv", index=False)

    pca = candidates[candidates["family"] == "pca"].copy()
    correlation, p_value = spearmanr(
        pca["explained_variance"], pca["stable_fraction"]
    )
    analysis = {
        "seed": seed,
        "candidate_pool": {
            "principal_components": PROJECTION_COMPONENTS,
            "fixed_random_directions": RANDOM_DIRECTIONS,
        },
        "selection_data": "calibration attacks only",
        "selection_rule": (
            "lexicographic maximum of minimum stable bucket and stable-image "
            "count, followed by minimum occupancy CV"
        ),
        "selected_direction": str(selected_row["direction"]),
        "selected_family": str(selected_row["family"]),
        "selected_stable_fraction": float(selected_row["stable_fraction"]),
        "selected_minimum_bucket": int(selected_row["minimum_bucket"]),
        "pc1_stable_fraction": float(pc1_stable.mean()),
        "pc1_minimum_bucket": int(
            np.bincount(pc1_labels[pc1_stable], minlength=16).min()
        ),
        "spearman_explained_variance_vs_stability": float(correlation),
        "spearman_p_value": float(p_value),
    }
    (OUTPUT / "boss_projection_analysis.json").write_text(
        json.dumps(analysis, indent=2), encoding="utf-8"
    )


def caltech_selection_analysis(dataset_root: Path, repeats: int) -> None:
    seed = 47
    dataset, _, clean, identifiers, attacked = prepare_embeddings(
        dataset_root,
        ROOT / "caltech101_results",
        "caltech101",
        seed,
        1500,
        7000,
        "RGB",
        256,
    )
    codebook = QuantileCodebook.fit(clean, 16)
    labels, stable = stability_metrics(codebook, clean, attacked)
    visual_features = dataset_statistics(dataset)
    index = build_qualified_index(
        codebook,
        identifiers,
        labels,
        stable,
        visual_features,
        seed,
    )
    _, messages = encrypted_messages(seed, 5, 8)
    protocol = NarcisProtocol(
        index,
        16,
        f"bossbase-{seed}".encode(),
        fec="reed_solomon",
        rs_parity=128,
    )
    selected_ids = []
    for _, _, encrypted in messages:
        selected_ids.extend(protocol.encode(encrypted).covers)
    positions = {name: offset for offset, name in enumerate(identifiers)}
    selected = np.asarray(
        [positions[name] for name in dict.fromkeys(selected_ids)], dtype=int
    )
    remaining = np.setdiff1d(np.arange(len(dataset)), selected)
    count = min(len(selected), len(remaining), 500)

    repeat_rows = []
    for repeat in range(repeats):
        local_seed = 47000 + repeat
        rng = np.random.default_rng(local_seed)
        positive = rng.choice(selected, count, replace=False)
        negative = rng.choice(remaining, count, replace=False)
        chosen = np.concatenate([positive, negative])
        targets = np.concatenate([np.ones(count), np.zeros(count)])
        images = []
        for position in chosen:
            image, _ = dataset[int(position)]
            images.append(
                F.interpolate(
                    image.unsqueeze(0),
                    size=(64, 64),
                    mode="bilinear",
                    align_corners=False,
                    antialias=True,
                ).squeeze(0)
            )
        images = torch.stack(images)
        train, test = train_test_split(
            np.arange(len(chosen)),
            test_size=0.35,
            random_state=local_seed,
            stratify=targets,
        )
        auc = cnn_selection_auc(
            images, targets, train, test, local_seed, 8
        )
        repeat_rows.append(
            {"repeat": repeat, "seed": local_seed, "cnn_auc": auc}
        )
    repeated = pd.DataFrame(repeat_rows)
    repeated.to_csv(
        OUTPUT / "caltech_seed47_cnn_repetitions.csv", index=False
    )

    all_features = dataset_statistics(dataset)
    binary = np.zeros(len(dataset), dtype=int)
    binary[selected] = 1
    scaler = StandardScaler()
    standard = scaler.fit_transform(all_features)
    model = LogisticRegression(max_iter=2000).fit(standard, binary)
    feature_names = (
        "mean_luminance",
        "luminance_std",
        "horizontal_gradient",
        "vertical_gradient",
        "entropy",
        "quantile_10",
        "quantile_90",
    )
    selected_mean = all_features[selected].mean(axis=0)
    other_mean = all_features[remaining].mean(axis=0)
    pooled = all_features.std(axis=0, ddof=1)
    feature_rows = []
    for offset, name in enumerate(feature_names):
        feature_rows.append(
            {
                "feature": name,
                "selected_mean": float(selected_mean[offset]),
                "nonselected_mean": float(other_mean[offset]),
                "standardized_mean_difference": float(
                    (selected_mean[offset] - other_mean[offset])
                    / max(pooled[offset], 1e-12)
                ),
                "standardized_logistic_coefficient": float(
                    model.coef_[0, offset]
                ),
            }
        )
    pd.DataFrame(feature_rows).to_csv(
        OUTPUT / "caltech_seed47_feature_shift.csv", index=False
    )

    categories = [Path(name).parent.name for name in identifiers]
    selected_counts = Counter(categories[position] for position in selected)
    other_counts = Counter(categories[position] for position in remaining)
    category_rows = []
    for category in sorted(set(categories)):
        selected_rate = selected_counts[category] / max(len(selected), 1)
        other_rate = other_counts[category] / max(len(remaining), 1)
        category_rows.append(
            {
                "category": category,
                "selected_fraction": selected_rate,
                "nonselected_fraction": other_rate,
                "difference": selected_rate - other_rate,
            }
        )
    pd.DataFrame(category_rows).sort_values(
        "difference", key=np.abs, ascending=False
    ).to_csv(OUTPUT / "caltech_seed47_category_shift.csv", index=False)

    mean, low, high = ci95(repeated["cnn_auc"].tolist())
    report = {
        "dataset": "Caltech-101",
        "partition_seed": seed,
        "unique_selected_covers": int(len(selected)),
        "repetitions": repeats,
        "cnn_auc_mean": mean,
        "cnn_auc_ci95_low": low,
        "cnn_auc_ci95_high": high,
        "cnn_auc_minimum": float(repeated["cnn_auc"].min()),
        "cnn_auc_maximum": float(repeated["cnn_auc"].max()),
    }
    (OUTPUT / "caltech_seed47_selection_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument(
        "--bossbase-root",
        type=Path,
        default=Path(
            r"C:\Users\User\Downloads\Compressed"
            r"\cpu_stego_experiments\datasets\BOSSbase"
        ),
    )
    parser.add_argument(
        "--caltech-root",
        type=Path,
        default=ROOT / "dataset_external" / "caltech101" / "images",
    )
    parser.add_argument(
        "--stage",
        choices=("payload", "boss", "caltech", "figures", "all"),
        default="all",
    )
    parser.add_argument("--detector-repeats", type=int, default=20)
    args = parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    if args.stage in {"payload", "all"}:
        payload_scalability()
    if args.stage in {"boss", "all"}:
        bossbase_ablation_and_projection(args.bossbase_root)
    if args.stage in {"caltech", "all"}:
        caltech_selection_analysis(
            args.caltech_root, args.detector_repeats
        )
    if args.stage in {"figures", "all"}:
        summary_figures()


if __name__ == "__main__":
    main()
