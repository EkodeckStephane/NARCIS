from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from .index import CoverIndex


@dataclass(frozen=True)
class DistributionBalanceDiagnostics:
    stable_fraction: float
    effective_sample_size: float
    maximum_weight: float
    minimum_weight: float
    mean_abs_smd_before: float
    mean_abs_smd_after: float
    max_abs_smd_before: float
    max_abs_smd_after: float


def _standardized_mean_difference(
    features: np.ndarray,
    selected: np.ndarray,
    weights: np.ndarray | None = None,
) -> np.ndarray:
    features = np.asarray(features, dtype=np.float64)
    selected = np.asarray(selected, dtype=bool)
    target_mean = features.mean(axis=0)
    scale = features.std(axis=0, ddof=1)
    scale = np.maximum(scale, 1e-12)
    selected_features = features[selected]
    if weights is None:
        selected_mean = selected_features.mean(axis=0)
    else:
        selected_weights = np.asarray(weights, dtype=np.float64)[selected]
        selected_mean = np.average(
            selected_features, axis=0, weights=selected_weights
        )
    return (selected_mean - target_mean) / scale


def stabilized_inverse_probability_weights(
    visual_features: np.ndarray,
    stable: np.ndarray,
    clip_low: float = 0.05,
    clip_high: float = 20.0,
) -> tuple[np.ndarray, DistributionBalanceDiagnostics]:
    visual_features = np.asarray(visual_features, dtype=np.float64)
    stable = np.asarray(stable, dtype=bool)
    if visual_features.ndim != 2:
        raise ValueError("visual_features must be a two-dimensional matrix")
    if len(visual_features) != len(stable):
        raise ValueError("stable mask must match visual_features")
    if clip_low <= 0 or clip_high <= clip_low:
        raise ValueError("invalid clipping interval")
    if stable.sum() == 0:
        raise ValueError("no attack-stable covers are available")
    if stable.all():
        weights = np.ones(len(stable), dtype=np.float64)
    else:
        scaler = StandardScaler()
        standardized = scaler.fit_transform(visual_features)
        model = LogisticRegression(max_iter=2000)
        model.fit(standardized, stable.astype(int))
        propensity = model.predict_proba(standardized)[:, 1]
        propensity = np.clip(propensity, 1e-4, 1.0)
        # Stable covers have density proportional to p(S=1|X) f(X).
        # Stabilized inverse-probability weighting p(S=1)/p(S=1|X)
        # therefore targets the full index distribution f(X).
        weights = stable.mean() / propensity
        weights = np.clip(weights, clip_low, clip_high)
        weights[~stable] = 0.0
        mean_stable_weight = weights[stable].mean()
        weights[stable] /= max(mean_stable_weight, 1e-12)

    stable_weights = weights[stable]
    ess = float(
        stable_weights.sum() ** 2
        / max(np.square(stable_weights).sum(), 1e-12)
    )
    before = _standardized_mean_difference(
        visual_features, stable, weights=None
    )
    after = _standardized_mean_difference(
        visual_features, stable, weights=weights
    )
    diagnostics = DistributionBalanceDiagnostics(
        stable_fraction=float(stable.mean()),
        effective_sample_size=ess,
        maximum_weight=float(stable_weights.max()),
        minimum_weight=float(stable_weights.min()),
        mean_abs_smd_before=float(np.mean(np.abs(before))),
        mean_abs_smd_after=float(np.mean(np.abs(after))),
        max_abs_smd_before=float(np.max(np.abs(before))),
        max_abs_smd_after=float(np.max(np.abs(after))),
    )
    return weights, diagnostics


def build_distribution_preserving_index(
    identifiers: list[str],
    clean_labels: np.ndarray,
    stable: np.ndarray,
    visual_features: np.ndarray,
    clip_low: float = 0.05,
    clip_high: float = 20.0,
) -> tuple[CoverIndex, DistributionBalanceDiagnostics]:
    clean_labels = np.asarray(clean_labels)
    stable = np.asarray(stable, dtype=bool)
    if len(identifiers) != len(clean_labels) or len(identifiers) != len(stable):
        raise ValueError("identifiers, labels, and stable mask must align")
    weights, diagnostics = stabilized_inverse_probability_weights(
        visual_features,
        stable,
        clip_low=clip_low,
        clip_high=clip_high,
    )
    positions = np.flatnonzero(stable)
    order = sorted(
        positions,
        key=lambda position: (
            int(clean_labels[position]),
            identifiers[position],
        ),
    )
    ordered = np.asarray(order, dtype=int)
    index = CoverIndex.build(
        [identifiers[position] for position in ordered],
        clean_labels[ordered],
        weights=weights[ordered],
    )
    return index, diagnostics
