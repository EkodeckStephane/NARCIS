import hashlib
import hmac

import numpy as np

from narcis.distribution_selection import DistributionMatchedScheduler


def _fixture(gamma: float = 0.0):
    paths = [f"image_{index:03d}.png" for index in range(100)]
    labels = np.zeros(100, dtype=int)
    strata = np.asarray([0] * 50 + [1] * 30 + [2] * 20)
    reliability = np.linspace(0.0, 1.0, 100)
    scheduler = DistributionMatchedScheduler.build(
        paths, labels, strata, reliability, gamma
    )
    return paths, strata, scheduler


def test_scheduler_preserves_stratum_proportions_in_prefixes():
    paths, strata, scheduler = _fixture(gamma=0.0)
    key = hashlib.sha256(b"selection-key").digest()
    context = hmac.new(key, b"payload", hashlib.sha256).digest()
    ordered = scheduler.order(0, paths, key, context)
    position = {path: index for index, path in enumerate(paths)}
    ordered_strata = np.asarray([strata[position[path]] for path in ordered])
    target = np.asarray([0.5, 0.3, 0.2])
    for prefix in (10, 20, 50, 100):
        observed = np.bincount(
            ordered_strata[:prefix], minlength=3
        ) / prefix
        assert np.max(np.abs(observed - target)) <= 0.1


def test_scheduler_is_deterministic_for_same_context():
    paths, _, scheduler = _fixture(gamma=4.0)
    key = hashlib.sha256(b"selection-key").digest()
    context = hashlib.sha256(b"same-context").digest()
    assert scheduler.order(0, paths, key, context) == scheduler.order(
        0, paths, key, context
    )


def test_scheduler_changes_order_with_payload_context():
    paths, _, scheduler = _fixture(gamma=4.0)
    key = hashlib.sha256(b"selection-key").digest()
    first = scheduler.order(0, paths, key, hashlib.sha256(b"A").digest())
    second = scheduler.order(0, paths, key, hashlib.sha256(b"B").digest())
    assert first != second


def test_reliability_only_changes_within_stratum_priority():
    paths, strata, neutral = _fixture(gamma=0.0)
    _, _, weighted = _fixture(gamma=12.0)
    key = hashlib.sha256(b"selection-key").digest()
    context = hashlib.sha256(b"payload").digest()
    neutral_order = neutral.order(0, paths, key, context)
    weighted_order = weighted.order(0, paths, key, context)
    position = {path: index for index, path in enumerate(paths)}
    neutral_strata = [strata[position[path]] for path in neutral_order]
    weighted_strata = [strata[position[path]] for path in weighted_order]
    assert neutral_strata == weighted_strata
    assert neutral_order != weighted_order
