import numpy as np

from narcis.group_bank import (
    build_balanced_group_bank,
    failure_masks,
    unavoidable_bad_group_lower_bound,
)


def test_failure_masks_encode_attack_failures():
    correct = np.array(
        [
            [True, False, True],
            [False, False, True],
            [True, True, True],
        ]
    )
    assert failure_masks(correct).tolist() == [2, 3, 0]


def test_lower_bound_matches_majority_capacity_argument():
    # 100 groups of five tolerate 200 failures per attack without a bad group.
    failures = np.array([200, 201, 278])
    lower = unavoidable_bad_group_lower_bound(failures, 100, 5)
    assert lower.tolist() == [0, 1, 26]


def test_group_bank_partitions_every_cover_exactly_once():
    labels = np.repeat(np.arange(2), 10)
    correct = np.ones((20, 4), dtype=bool)
    banks, diagnostics = build_balanced_group_bank(
        labels,
        correct,
        label_count=2,
        group_size=5,
        seed=17,
        restarts=2,
        swap_steps=100,
    )
    for label in range(2):
        flattened = [cover for group in banks[label] for cover in group]
        expected = set(np.flatnonzero(labels == label).tolist())
        assert len(banks[label]) == 2
        assert all(len(group) == 5 for group in banks[label])
        assert len(flattened) == len(set(flattened)) == 10
        assert set(flattened) == expected
        assert diagnostics[label].reaches_lower_bound


def test_group_bank_concentrates_unavoidable_majority_failures():
    # One label, 100 groups, 278 covers fail the only attack. The analytical
    # minimum is ceil((278 - 2*100) / 3) = 26 majority-failing groups.
    labels = np.zeros(500, dtype=int)
    correct = np.ones((500, 1), dtype=bool)
    correct[:278, 0] = False
    banks, diagnostics = build_balanced_group_bank(
        labels,
        correct,
        label_count=1,
        group_size=5,
        seed=23,
        restarts=4,
        swap_steps=1000,
    )
    assert len(banks[0]) == 100
    assert diagnostics[0].lower_bound_by_attack == (26,)
    assert diagnostics[0].bad_groups_by_attack == (26,)
    assert diagnostics[0].reaches_lower_bound


def test_group_bank_is_deterministic_for_fixed_seed():
    rng = np.random.default_rng(9)
    labels = np.repeat(np.arange(2), 20)
    correct = rng.random((40, 3)) > 0.15
    first, _ = build_balanced_group_bank(
        labels,
        correct,
        label_count=2,
        group_size=5,
        seed=99,
        restarts=2,
        swap_steps=200,
    )
    second, _ = build_balanced_group_bank(
        labels,
        correct,
        label_count=2,
        group_size=5,
        seed=99,
        restarts=2,
        swap_steps=200,
    )
    assert first == second
