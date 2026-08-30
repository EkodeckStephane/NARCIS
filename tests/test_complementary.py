from collections import Counter

import numpy as np

from narcis.complementary import (
    attack_failure_masks,
    build_clean_strata,
    complementary_triplet_masks,
    select_complementary_triplet,
)


def test_failure_masks_encode_attack_disagreements():
    clean = np.array([1, 1, 2])
    attacked = np.array(
        [
            [1, 0, 1],
            [0, 1, 1],
            [2, 2, 0],
        ]
    )
    masks = attack_failure_masks(clean, attacked)
    assert masks.tolist() == [2, 1, 4]


def test_pairwise_disjoint_masks_are_exact_triplet_condition():
    assert complementary_triplet_masks(0b001, 0b010, 0b100)
    assert not complementary_triplet_masks(0b001, 0b011, 0b100)


def test_selector_returns_attack_complementary_distinct_triplet():
    positions = np.arange(6)
    masks = np.array([0b001, 0b010, 0b100, 0b001, 0b010, 0b100])
    strata = np.array([0, 1, 2, 0, 1, 2])
    identifiers = [f"image-{index}" for index in positions]
    triplet = select_complementary_triplet(
        candidate_positions=positions,
        failure_masks=masks,
        strata=strata,
        identifiers=identifiers,
        codebook_label=3,
        selection_key=b"secret-selection-key",
        context=b"session-context",
        used_positions=set(),
        stratum_used=Counter(),
    )
    assert len(set(triplet)) == 3
    selected_masks = [int(masks[position]) for position in triplet]
    assert complementary_triplet_masks(*selected_masks)


def test_selector_does_not_reuse_positions():
    positions = np.arange(6)
    masks = np.array([0b001, 0b010, 0b100, 0b001, 0b010, 0b100])
    strata = np.array([0, 1, 2, 0, 1, 2])
    identifiers = [f"image-{index}" for index in positions]
    triplet = select_complementary_triplet(
        candidate_positions=positions,
        failure_masks=masks,
        strata=strata,
        identifiers=identifiers,
        codebook_label=1,
        selection_key=b"secret-selection-key",
        context=b"another-session",
        used_positions={0, 1, 2},
        stratum_used=Counter(),
    )
    assert set(triplet) == {3, 4, 5}


def test_clean_strata_are_deterministic():
    rng = np.random.default_rng(17)
    clean = rng.normal(size=(256, 12))
    visual = rng.normal(size=(256, 7))
    first = build_clean_strata(clean, visual, seed=11, clusters=8, pca_dimensions=4)
    second = build_clean_strata(clean, visual, seed=11, clusters=8, pca_dimensions=4)
    assert first.standardized_features.shape == (256, 11)
    assert np.array_equal(first.labels, second.labels)
