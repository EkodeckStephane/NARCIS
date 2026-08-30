from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .group_bank import unavoidable_bad_group_lower_bound
from .index import QuantileCodebook
from .selection import stabilized_inverse_probability_weights
from .tomm_evaluation import _candidate_directions


@dataclass(frozen=True)
class GroupBankProjectionChoice:
    name: str
    family: str
    direction: np.ndarray
    codebook: QuantileCodebook
    labels: np.ndarray
    calibration_correct: np.ndarray
    stable: np.ndarray
    max_unavoidable_bad_fraction: float
    sum_unavoidable_bad_fraction: float


def select_group_bank_projection(
    clean: np.ndarray,
    attacked_calibration: dict[str, np.ndarray],
    visual_features: np.ndarray,
    clusters: int = 8,
    group_size: int = 5,
    principal_components: int = 16,
    random_directions: int = 32,
    random_seed: int = 20260828,
) -> tuple[GroupBankProjectionChoice, pd.DataFrame]:
    """Select the frozen TOMM projection using calibration information only.

    Ranking minimizes the analytically unavoidable majority-failing group
    fraction before using stable-cover count and IPW balance diagnostics as
    deterministic secondary criteria. Holdout attacks and detector outputs are
    absent from this function by construction.
    """
    if clusters < 2 or clusters & (clusters - 1):
        raise ValueError("clusters must be a power of two")
    if group_size < 3 or group_size % 2 == 0:
        raise ValueError("group_size must be an odd integer >= 3")
    if len(clean) != len(visual_features):
        raise ValueError("clean and visual_features must align")
    for name, embeddings in attacked_calibration.items():
        if len(embeddings) != len(clean):
            raise ValueError(f"calibration attack {name} does not align with clean embeddings")

    attack_names = tuple(attacked_calibration)
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
            clean,
            clusters,
            candidate["direction"],
        )
        labels = codebook.predict(clean)
        counts = np.bincount(labels, minlength=clusters)
        compatible = bool(np.all(counts > 0) and np.all(counts % group_size == 0))
        correct = np.stack(
            [codebook.predict(attacked_calibration[name]) == labels for name in attack_names],
            axis=1,
        )
        stable = correct.all(axis=1)
        unavoidable = np.zeros((clusters, len(attack_names)), dtype=int)
        total_groups = 0
        for label in range(clusters):
            positions = np.flatnonzero(labels == label)
            group_count = len(positions) // group_size
            total_groups += group_count
            if group_count:
                failures = (~correct[positions]).sum(axis=0)
                unavoidable[label] = unavoidable_bad_group_lower_bound(
                    failures,
                    group_count,
                    group_size,
                )
        fractions = unavoidable.sum(axis=0) / max(total_groups, 1)

        if stable.any():
            _, balance = stabilized_inverse_probability_weights(
                visual_features,
                stable,
            )
            mean_smd = balance.mean_abs_smd_after
            max_smd = balance.max_abs_smd_after
        else:
            mean_smd = float("inf")
            max_smd = float("inf")

        row = {
            "direction": candidate["name"],
            "family": candidate["family"],
            "compatible": compatible,
            "clean_min_bucket": int(counts.min()),
            "clean_max_bucket": int(counts.max()),
            "max_unavoidable_bad_fraction": float(fractions.max()),
            "sum_unavoidable_bad_fraction": float(fractions.sum()),
            "stable_images": int(stable.sum()),
            "stable_fraction": float(stable.mean()),
            "mean_abs_smd_after_ipw": float(mean_smd),
            "max_abs_smd_after_ipw": float(max_smd),
            "explained_variance": candidate["explained_variance"],
        }
        for attack_index, attack_name in enumerate(attack_names):
            row[f"unavoidable_bad_fraction__{attack_name}"] = float(
                fractions[attack_index]
            )
        rows.append(row)
        retained[candidate["name"]] = (
            candidate,
            codebook,
            labels,
            correct,
            stable,
            fractions,
        )

    frame = pd.DataFrame(rows)
    compatible_frame = frame[frame["compatible"]].copy()
    if compatible_frame.empty:
        raise RuntimeError("no group-bank-compatible projection candidate")
    ranked = compatible_frame.sort_values(
        [
            "max_unavoidable_bad_fraction",
            "sum_unavoidable_bad_fraction",
            "stable_images",
            "max_abs_smd_after_ipw",
            "mean_abs_smd_after_ipw",
            "direction",
        ],
        ascending=[True, True, False, True, True, True],
        kind="mergesort",
    )
    selected_name = str(ranked.iloc[0]["direction"])
    candidate, codebook, labels, correct, stable, fractions = retained[selected_name]
    choice = GroupBankProjectionChoice(
        name=selected_name,
        family=str(candidate["family"]),
        direction=np.asarray(candidate["direction"], dtype=np.float64),
        codebook=codebook,
        labels=labels,
        calibration_correct=correct,
        stable=stable,
        max_unavoidable_bad_fraction=float(fractions.max()),
        sum_unavoidable_bad_fraction=float(fractions.sum()),
    )
    return choice, frame
