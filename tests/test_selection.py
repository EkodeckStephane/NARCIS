import numpy as np
import pytest

from narcis.selection import (
    build_distribution_preserving_index,
    stabilized_inverse_probability_weights,
)


def test_ipw_reduces_synthetic_selection_imbalance():
    rng = np.random.default_rng(20260828)
    features = rng.normal(size=(6000, 3))
    logits = 1.8 * features[:, 0] - 1.1 * features[:, 1]
    probability = 1.0 / (1.0 + np.exp(-logits))
    stable = rng.random(len(features)) < probability
    _, diagnostics = stabilized_inverse_probability_weights(
        features, stable
    )
    assert diagnostics.mean_abs_smd_after < diagnostics.mean_abs_smd_before
    assert diagnostics.max_abs_smd_after < diagnostics.max_abs_smd_before


def test_distribution_preserving_index_retains_only_stable_covers():
    identifiers = ["a", "b", "c", "d"]
    labels = np.array([0, 0, 1, 1])
    stable = np.array([True, False, True, False])
    features = np.array(
        [
            [0.0, 0.0],
            [1.0, 1.0],
            [0.2, -0.1],
            [1.3, 0.9],
        ]
    )
    index, diagnostics = build_distribution_preserving_index(
        identifiers, labels, stable, features
    )
    assert set(index.labels) == {"a", "c"}
    assert set(index.weights) == {"a", "c"}
    assert diagnostics.stable_fraction == pytest.approx(0.5)


def test_ipw_handles_all_stable_covers_with_unit_weights():
    features = np.arange(12, dtype=float).reshape(6, 2)
    stable = np.ones(6, dtype=bool)
    weights, diagnostics = stabilized_inverse_probability_weights(
        features, stable
    )
    assert np.allclose(weights, 1.0)
    assert diagnostics.mean_abs_smd_after == pytest.approx(0.0)


def test_ipw_rejects_empty_stable_set():
    with pytest.raises(ValueError, match="no attack-stable"):
        stabilized_inverse_probability_weights(
            np.zeros((4, 2)),
            np.zeros(4, dtype=bool),
        )
