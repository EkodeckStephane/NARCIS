from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import hmac

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class CleanStrata:
    standardized_features: np.ndarray
    labels: np.ndarray


def attack_failure_masks(
    clean_labels: np.ndarray,
    attacked_labels: np.ndarray,
) -> np.ndarray:
    """Encode per-cover calibration failures as an integer bit mask.

    ``attacked_labels`` has shape ``(n_covers, n_attacks)``. Bit ``a`` is set
    exactly when the clean label is not recovered under calibration attack
    ``a``. The implementation currently uses uint64, allowing up to 64
    calibration attacks without changing the representation.
    """
    clean_labels = np.asarray(clean_labels)
    attacked_labels = np.asarray(attacked_labels)
    if attacked_labels.ndim != 2:
        raise ValueError("attacked_labels must be a two-dimensional matrix")
    if len(clean_labels) != len(attacked_labels):
        raise ValueError("clean and attacked labels must align")
    if attacked_labels.shape[1] > 64:
        raise ValueError("at most 64 calibration attacks are supported")
    masks = np.zeros(len(clean_labels), dtype=np.uint64)
    for attack in range(attacked_labels.shape[1]):
        failed = attacked_labels[:, attack] != clean_labels
        masks |= failed.astype(np.uint64) << np.uint64(attack)
    return masks


def complementary_triplet_masks(first: int, second: int, third: int) -> bool:
    """Return True iff no calibration attack is failed by two covers."""
    return not (
        (int(first) & int(second))
        or (int(first) & int(third))
        or (int(second) & int(third))
    )


def build_clean_strata(
    clean_embeddings: np.ndarray,
    visual_features: np.ndarray,
    seed: int,
    clusters: int = 32,
    pca_dimensions: int = 8,
) -> CleanStrata:
    clean_embeddings = np.asarray(clean_embeddings, dtype=np.float64)
    visual_features = np.asarray(visual_features, dtype=np.float64)
    if len(clean_embeddings) != len(visual_features):
        raise ValueError("clean embeddings and visual features must align")
    centered = clean_embeddings - clean_embeddings.mean(axis=0)
    _, _, right = np.linalg.svd(centered, full_matrices=False)
    dimensions = min(pca_dimensions, right.shape[0])
    scores = centered @ right[:dimensions].T
    features = np.concatenate([visual_features, scores], axis=1)
    standardized = StandardScaler().fit_transform(features)
    labels = KMeans(
        n_clusters=clusters,
        random_state=20260828 + int(seed),
        n_init=20,
    ).fit_predict(standardized)
    return CleanStrata(standardized, labels.astype(np.int32))


def _hmac_priority(
    key: bytes,
    context: bytes,
    codebook_label: int,
    identifier: str,
) -> bytes:
    return hmac.new(
        key,
        b"complementary-candidate:"
        + context
        + int(codebook_label).to_bytes(4, "big", signed=False)
        + identifier.encode("utf-8"),
        hashlib.sha256,
    ).digest()


def _candidate_preference(
    position: int,
    step: int,
    strata: np.ndarray,
    stratum_used: Counter,
    target: dict[int, float],
    priority: dict[int, bytes],
) -> tuple[float, bytes, int]:
    stratum = int(strata[position])
    selected_before = sum(stratum_used.values())
    deficit = target.get(stratum, 0.0) * (selected_before + step) - stratum_used[stratum]
    # min() is used by the caller, so negate the desired largest deficit.
    return -float(deficit), priority[position], int(position)


def select_complementary_triplet(
    *,
    candidate_positions: np.ndarray,
    failure_masks: np.ndarray,
    strata: np.ndarray,
    identifiers: list[str],
    codebook_label: int,
    selection_key: bytes,
    context: bytes,
    used_positions: set[int],
    stratum_used: Counter,
) -> tuple[int, int, int]:
    """Select one robust triplet without detector-derived optimization.

    The target stratum distribution is the natural distribution among all
    covers carrying the requested clean codebook label. Selection then uses
    current proportional stratum deficit followed by a secret HMAC tie-break.
    The three failure masks must be pairwise disjoint, which is equivalent to
    a correct majority under every calibration attack for repetition three.
    """
    candidate_positions = np.asarray(candidate_positions, dtype=int)
    available = [
        int(position)
        for position in candidate_positions
        if int(position) not in used_positions
    ]
    if len(available) < 3:
        raise ValueError("insufficient unused covers for a complementary triplet")

    counts = Counter(int(strata[position]) for position in candidate_positions)
    total = len(candidate_positions)
    target = {stratum: count / total for stratum, count in counts.items()}
    priority = {
        position: _hmac_priority(
            selection_key,
            context,
            codebook_label,
            identifiers[position],
        )
        for position in available
    }

    first_order = sorted(
        available,
        key=lambda position: _candidate_preference(
            position, 1, strata, stratum_used, target, priority
        ),
    )
    for first in first_order:
        first_mask = int(failure_masks[first])
        second_order = sorted(
            (
                second
                for second in available
                if second != first
                and not (first_mask & int(failure_masks[second]))
            ),
            key=lambda position: _candidate_preference(
                position, 2, strata, stratum_used, target, priority
            ),
        )
        for second in second_order:
            union = first_mask | int(failure_masks[second])
            third_candidates = [
                third
                for third in available
                if third not in {first, second}
                and not (union & int(failure_masks[third]))
            ]
            if not third_candidates:
                continue
            third = min(
                third_candidates,
                key=lambda position: _candidate_preference(
                    position, 3, strata, stratum_used, target, priority
                ),
            )
            return int(first), int(second), int(third)

    raise ValueError(
        f"no complementary triplet exists for codebook label {codebook_label}"
    )
