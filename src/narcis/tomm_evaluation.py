from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .attacks import attack_suite
from .glcm import glcm_texture_features
from .index import CoverIndex, QuantileCodebook
from .protocol import NarcisProtocol
from .security import decrypt_payload
from .selection import (
    DistributionBalanceDiagnostics,
    build_distribution_preserving_index,
)


@dataclass(frozen=True)
class ProjectionChoice:
    name: str
    family: str
    direction: np.ndarray
    codebook: QuantileCodebook
    labels: np.ndarray
    stable: np.ndarray
    index: CoverIndex
    diagnostics: DistributionBalanceDiagnostics


def _candidate_directions(
    clean: np.ndarray,
    principal_components: int,
    random_directions: int,
    random_seed: int,
) -> list[dict]:
    centered = clean - clean.mean(axis=0)
    _, singular, right = np.linalg.svd(centered, full_matrices=False)
    explained = singular**2 / max(float(np.sum(singular**2)), 1e-12)
    candidates = [
        {
            "name": f"pc{offset + 1}",
            "family": "pca",
            "direction": right[offset].astype(np.float64),
            "explained_variance": float(explained[offset]),
        }
        for offset in range(min(principal_components, len(right)))
    ]
    rng = np.random.default_rng(random_seed)
    for offset in range(random_directions):
        direction = rng.normal(size=clean.shape[1])
        direction /= max(float(np.linalg.norm(direction)), 1e-12)
        candidates.append(
            {
                "name": f"random_{offset + 1:02d}",
                "family": "fixed_random",
                "direction": direction,
                "explained_variance": float("nan"),
            }
        )
    return candidates


def _stability(
    codebook: QuantileCodebook,
    clean: np.ndarray,
    attacked: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    labels = codebook.predict(clean)
    stable = np.ones(len(clean), dtype=bool)
    for embeddings in attacked.values():
        stable &= codebook.predict(embeddings) == labels
    return labels, stable


def select_calibration_locked_projection(
    clean: np.ndarray,
    attacked_calibration: dict[str, np.ndarray],
    identifiers: list[str],
    visual_features: np.ndarray,
    clusters: int,
    principal_components: int = 16,
    random_directions: int = 32,
    random_seed: int = 20260828,
) -> tuple[ProjectionChoice, pd.DataFrame]:
    """Choose a projection using calibration information only.

    Candidate ranking is lexicographic: first preserve finite-index feasibility
    by maximizing the minimum stable bucket, then stable-image count, then
    minimize post-IPW feature imbalance, then occupancy imbalance. No holdout
    attack outcomes or detector AUCs are used to choose the direction.
    """
    candidates = _candidate_directions(
        clean,
        principal_components,
        random_directions,
        random_seed,
    )
    rows: list[dict] = []
    retained: dict[str, tuple] = {}
    for candidate in candidates:
        codebook = QuantileCodebook.fit_direction(
            clean, clusters, candidate["direction"]
        )
        labels, stable = _stability(codebook, clean, attacked_calibration)
        counts = np.bincount(labels[stable], minlength=clusters)
        if stable.any():
            index, diagnostics = build_distribution_preserving_index(
                identifiers,
                labels,
                stable,
                visual_features,
            )
            mean_smd = diagnostics.mean_abs_smd_after
            max_smd = diagnostics.max_abs_smd_after
            ess = diagnostics.effective_sample_size
        else:
            index = CoverIndex({}, {}, {})
            diagnostics = DistributionBalanceDiagnostics(
                stable_fraction=0.0,
                effective_sample_size=0.0,
                maximum_weight=float("nan"),
                minimum_weight=float("nan"),
                mean_abs_smd_before=float("inf"),
                mean_abs_smd_after=float("inf"),
                max_abs_smd_before=float("inf"),
                max_abs_smd_after=float("inf"),
            )
            mean_smd = float("inf")
            max_smd = float("inf")
            ess = 0.0
        occupancy_cv = float(
            counts.std() / max(float(counts.mean()), 1e-12)
        )
        row = {
            "direction": candidate["name"],
            "family": candidate["family"],
            "explained_variance": candidate["explained_variance"],
            "stable_images": int(stable.sum()),
            "stable_fraction": float(stable.mean()),
            "minimum_bucket": int(counts.min()),
            "median_bucket": float(np.median(counts)),
            "maximum_bucket": int(counts.max()),
            "occupancy_cv": occupancy_cv,
            "ipw_effective_sample_size": ess,
            "mean_abs_smd_after_ipw": mean_smd,
            "max_abs_smd_after_ipw": max_smd,
        }
        rows.append(row)
        retained[candidate["name"]] = (
            candidate,
            codebook,
            labels,
            stable,
            index,
            diagnostics,
        )

    frame = pd.DataFrame(rows)
    ranked = frame.sort_values(
        [
            "minimum_bucket",
            "stable_images",
            "max_abs_smd_after_ipw",
            "mean_abs_smd_after_ipw",
            "occupancy_cv",
            "direction",
        ],
        ascending=[False, False, True, True, True, True],
        kind="mergesort",
    )
    selected_name = str(ranked.iloc[0]["direction"])
    candidate, codebook, labels, stable, index, diagnostics = retained[
        selected_name
    ]
    choice = ProjectionChoice(
        name=selected_name,
        family=str(candidate["family"]),
        direction=np.asarray(candidate["direction"], dtype=np.float64),
        codebook=codebook,
        labels=labels,
        stable=stable,
        index=index,
        diagnostics=diagnostics,
    )
    return choice, frame


def _dataset_image(dataset, position: int) -> torch.Tensor:
    image, _ = dataset[position]
    return image


def glcm_selection_auc(
    dataset,
    identifiers: list[str],
    selected_ids: list[str],
    seed: int,
    maximum_per_class: int = 500,
) -> dict:
    positions = {name: offset for offset, name in enumerate(identifiers)}
    unique_selected = [name for name in dict.fromkeys(selected_ids) if name in positions]
    selected = np.asarray([positions[name] for name in unique_selected], dtype=int)
    remaining = np.setdiff1d(np.arange(len(dataset)), selected)
    count = min(len(selected), len(remaining), maximum_per_class)
    if count < 10:
        return {
            "detector_samples_per_class": int(count),
            "glcm_auc": float("nan"),
            "glcm_feature_count": 5,
        }

    rng = np.random.default_rng(seed)
    positive = rng.choice(selected, count, replace=False)
    negative = rng.choice(remaining, count, replace=False)
    chosen = np.concatenate([positive, negative])
    targets = np.concatenate([np.ones(count), np.zeros(count)])
    features = np.stack(
        [glcm_texture_features(_dataset_image(dataset, int(position)).numpy())
         for position in chosen]
    )
    train, test = train_test_split(
        np.arange(len(chosen)),
        test_size=0.35,
        random_state=seed,
        stratify=targets,
    )
    classifier = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=2000, class_weight="balanced"),
    )
    classifier.fit(features[train], targets[train])
    probabilities = classifier.predict_proba(features[test])[:, 1]
    return {
        "detector_samples_per_class": int(count),
        "glcm_auc": float(roc_auc_score(targets[test], probabilities)),
        "glcm_feature_count": int(features.shape[1]),
    }


def run_real_payload_channel(
    *,
    dataset_name: str,
    dataset,
    model: torch.nn.Module,
    model_size: int,
    channel_size: int,
    identifiers: list[str],
    choice: ProjectionChoice,
    encrypted_message_factory,
    seed: int,
    payload_sizes: tuple[int, ...] = (8, 32, 64),
    messages_per_size: int = 10,
    rs_parity: int = 128,
) -> tuple[pd.DataFrame, list[str]]:
    """Run real images through the complete channel for each payload size."""
    from run_bossbase_campaign import model_view

    path_positions = {name: offset for offset, name in enumerate(identifiers)}
    suite = attack_suite(channel_size, seed)
    rows: list[dict] = []
    selected_ids: list[str] = []

    for payload_bytes in payload_sizes:
        key, messages = encrypted_message_factory(
            seed + payload_bytes * 1000,
            messages_per_size,
            payload_bytes,
        )
        protocol = NarcisProtocol(
            choice.index,
            choice.codebook.size,
            f"{dataset_name}-{seed}-tomm".encode(),
            fec="reed_solomon",
            rs_parity=rs_parity,
        )
        for sequence, plaintext, encrypted in messages:
            feasible, deficits = protocol.feasibility(encrypted)
            if not feasible:
                rows.append(
                    {
                        "dataset": dataset_name,
                        "seed": seed,
                        "payload_bytes": payload_bytes,
                        "sequence": sequence,
                        "attack": "preflight",
                        "clusters": choice.codebook.size,
                        "bits_per_symbol": int(math.log2(choice.codebook.size)),
                        "covers": 0,
                        "symbol_accuracy": float("nan"),
                        "message_success": 0,
                        "rs_corrections": -1,
                        "feasible": 0,
                        "deficit_symbols": int(sum(deficits.values())),
                    }
                )
                continue

            transmission = protocol.encode(encrypted)
            selected_ids.extend(transmission.covers)
            native = torch.stack(
                [
                    _dataset_image(dataset, path_positions[path])
                    for path in transmission.covers
                ]
            )
            intended = np.asarray(
                [choice.index.labels[path] for path in transmission.covers]
            )
            for attack_name, attack in suite.items():
                damaged = torch.stack([attack(image) for image in native])
                with torch.no_grad():
                    embeddings = model(model_view(damaged, model_size)).cpu().numpy()
                received = choice.codebook.predict(embeddings)
                try:
                    recovered_encrypted, corrections = protocol.decode_labels(
                        received.tolist(), transmission.padding_bits
                    )
                    recovered = decrypt_payload(
                        recovered_encrypted,
                        key,
                        sequence,
                    )
                    success = recovered == plaintext
                except Exception:
                    corrections = -1
                    success = False
                rows.append(
                    {
                        "dataset": dataset_name,
                        "seed": seed,
                        "payload_bytes": payload_bytes,
                        "sequence": sequence,
                        "attack": attack_name,
                        "clusters": choice.codebook.size,
                        "bits_per_symbol": int(math.log2(choice.codebook.size)),
                        "covers": len(transmission.covers),
                        "symbol_accuracy": float(np.mean(received == intended)),
                        "message_success": int(success),
                        "rs_corrections": corrections,
                        "feasible": 1,
                        "deficit_symbols": 0,
                    }
                )
    return pd.DataFrame(rows), selected_ids


def summarize_payload_trials(raw: pd.DataFrame) -> pd.DataFrame:
    valid = raw[raw["attack"] != "preflight"].copy()
    if valid.empty:
        return pd.DataFrame()
    return (
        valid.groupby(
            ["dataset", "seed", "payload_bytes", "attack"],
            as_index=False,
        )
        .agg(
            trials=("message_success", "size"),
            successes=("message_success", "sum"),
            message_success=("message_success", "mean"),
            mean_symbol_accuracy=("symbol_accuracy", "mean"),
            minimum_symbol_accuracy=("symbol_accuracy", "min"),
            mean_covers=("covers", "mean"),
            maximum_rs_corrections=("rs_corrections", "max"),
        )
    )


def write_choice_manifest(
    choice: ProjectionChoice,
    destination: Path,
    dataset_name: str,
    seed: int,
) -> None:
    import json

    destination.write_text(
        json.dumps(
            {
                "dataset": dataset_name,
                "seed": seed,
                "direction": choice.name,
                "family": choice.family,
                "clusters": choice.codebook.size,
                "stable_images": int(choice.stable.sum()),
                "stable_fraction": float(choice.stable.mean()),
                "distribution_balance": {
                    "effective_sample_size": choice.diagnostics.effective_sample_size,
                    "minimum_weight": choice.diagnostics.minimum_weight,
                    "maximum_weight": choice.diagnostics.maximum_weight,
                    "mean_abs_smd_before": choice.diagnostics.mean_abs_smd_before,
                    "mean_abs_smd_after": choice.diagnostics.mean_abs_smd_after,
                    "max_abs_smd_before": choice.diagnostics.max_abs_smd_before,
                    "max_abs_smd_after": choice.diagnostics.max_abs_smd_after,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
