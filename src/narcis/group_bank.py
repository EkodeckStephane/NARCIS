from __future__ import annotations

from dataclasses import dataclass
from collections import Counter

import numpy as np


@dataclass(frozen=True)
class GroupBankDiagnostics:
    label: int
    covers: int
    groups: int
    group_size: int
    bad_groups_by_attack: tuple[int, ...]
    lower_bound_by_attack: tuple[int, ...]

    @property
    def reaches_lower_bound(self) -> bool:
        return self.bad_groups_by_attack == self.lower_bound_by_attack


def failure_masks(correct: np.ndarray) -> np.ndarray:
    """Encode per-cover calibration failures as compact integer bitmasks."""
    correct = np.asarray(correct, dtype=bool)
    if correct.ndim != 2:
        raise ValueError("correct must be a two-dimensional cover-by-attack matrix")
    if correct.shape[1] > 63:
        raise ValueError("at most 63 calibration attacks are supported")
    masks = np.zeros(len(correct), dtype=np.uint64)
    for attack in range(correct.shape[1]):
        masks |= ((~correct[:, attack]).astype(np.uint64) << np.uint64(attack))
    return masks


def _failure_bits(masks: np.ndarray, attack_count: int) -> np.ndarray:
    masks = np.asarray(masks, dtype=np.uint64)
    return np.asarray(
        [[(int(mask) >> attack) & 1 for attack in range(attack_count)] for mask in masks],
        dtype=np.int8,
    )


def unavoidable_bad_group_lower_bound(
    failures: np.ndarray,
    groups: int,
    group_size: int,
) -> np.ndarray:
    """Return a per-attack lower bound on majority-failing groups.

    A majority-correct group of odd size r may contain at most floor((r-1)/2)
    failing covers. Any failures beyond that aggregate good-group capacity must
    be concentrated in majority-failing groups. A failing group can absorb at
    most r failures, i.e. r-t failures beyond the good-group allowance t.
    """
    if group_size < 3 or group_size % 2 == 0:
        raise ValueError("group_size must be an odd integer >= 3")
    failures = np.asarray(failures, dtype=int)
    tolerance = (group_size - 1) // 2
    excess = np.maximum(0, failures - tolerance * groups)
    return np.ceil(excess / (group_size - tolerance)).astype(int)


def _initial_partition(
    indices: np.ndarray,
    bits: np.ndarray,
    group_size: int,
    rng: np.random.Generator,
) -> tuple[list[list[int]], np.ndarray]:
    group_count = len(indices) // group_size
    difficulty = bits[indices].sum(axis=1) + rng.random(len(indices)) * 0.01
    order = indices[np.argsort(-difficulty)]
    sizes = np.zeros(group_count, dtype=int)
    counts = np.zeros((group_count, bits.shape[1]), dtype=int)
    groups: list[list[int]] = [[] for _ in range(group_count)]
    majority = group_size // 2 + 1

    for index in order:
        cover_bits = bits[index]
        candidates = np.flatnonzero(sizes < group_size)
        before = counts[candidates] >= majority
        after = (counts[candidates] + cover_bits) >= majority
        newly_bad = (after & ~before).sum(axis=1)
        overlap_with_bad = (before & (cover_bits[None, :] > 0)).sum(axis=1)
        total_failure_load = (counts[candidates] + cover_bits).sum(axis=1)
        # Lexicographic objective:
        #   1. avoid creating a new majority-failing group/attack;
        #   2. when failures are unavoidable, concentrate them in already-bad
        #      group/attack cells instead of contaminating additional groups;
        #   3. keep group occupancy balanced;
        #   4. deterministic random tie-break from the frozen construction seed.
        choice = min(
            zip(
                newly_bad.tolist(),
                (-overlap_with_bad).tolist(),
                total_failure_load.tolist(),
                sizes[candidates].tolist(),
                rng.random(len(candidates)).tolist(),
                candidates.tolist(),
            )
        )[-1]
        group = int(choice)
        groups[group].append(int(index))
        sizes[group] += 1
        counts[group] += cover_bits

    return groups, counts


def _improve_by_swaps(
    groups: list[list[int]],
    counts: np.ndarray,
    bits: np.ndarray,
    group_size: int,
    rng: np.random.Generator,
    steps: int,
) -> tuple[list[list[int]], np.ndarray]:
    majority = group_size // 2 + 1
    for _ in range(steps):
        first_group, second_group = rng.choice(len(groups), 2, replace=False)
        first_position = int(rng.integers(group_size))
        second_position = int(rng.integers(group_size))
        first = groups[first_group][first_position]
        second = groups[second_group][second_position]

        first_new = counts[first_group] - bits[first] + bits[second]
        second_new = counts[second_group] - bits[second] + bits[first]
        old_cost = int(
            (counts[first_group] >= majority).sum()
            + (counts[second_group] >= majority).sum()
        )
        new_cost = int(
            (first_new >= majority).sum()
            + (second_new >= majority).sum()
        )
        if new_cost < old_cost or (new_cost == old_cost and rng.random() < 0.001):
            groups[first_group][first_position] = second
            groups[second_group][second_position] = first
            counts[first_group] = first_new
            counts[second_group] = second_new

    return groups, counts


def build_balanced_group_bank(
    labels: np.ndarray,
    correct: np.ndarray,
    *,
    label_count: int,
    group_size: int = 5,
    seed: int = 20260830,
    restarts: int = 10,
    swap_steps: int = 6000,
) -> tuple[dict[int, tuple[tuple[int, ...], ...]], tuple[GroupBankDiagnostics, ...]]:
    """Partition every label bucket into complementary majority groups.

    Construction uses calibration correctness only. Every cover is used exactly
    once in its label's bank. The objective minimizes the number of groups whose
    majority label can fail under each calibration attack. Detector outputs,
    holdout attacks, and payload results are not used by this function.
    """
    labels = np.asarray(labels, dtype=int)
    correct = np.asarray(correct, dtype=bool)
    if len(labels) != len(correct):
        raise ValueError("labels and correct must have the same number of covers")
    if group_size < 3 or group_size % 2 == 0:
        raise ValueError("group_size must be an odd integer >= 3")
    if restarts < 1 or swap_steps < 0:
        raise ValueError("invalid optimization budget")

    masks = failure_masks(correct)
    bits = _failure_bits(masks, correct.shape[1])
    majority = group_size // 2 + 1
    banks: dict[int, tuple[tuple[int, ...], ...]] = {}
    diagnostics: list[GroupBankDiagnostics] = []

    for label in range(label_count):
        indices = np.flatnonzero(labels == label)
        if len(indices) == 0 or len(indices) % group_size:
            raise ValueError(
                f"label {label} contains {len(indices)} covers; "
                f"group_size={group_size} requires a positive divisible bucket"
            )
        group_count = len(indices) // group_size
        attack_failures = (~correct[indices]).sum(axis=0)
        lower_bound = unavoidable_bad_group_lower_bound(
            attack_failures,
            group_count,
            group_size,
        )

        best = None
        for restart in range(restarts):
            rng = np.random.default_rng(seed + label * 1009 + restart)
            groups, counts = _initial_partition(indices, bits, group_size, rng)
            groups, counts = _improve_by_swaps(
                groups,
                counts,
                bits,
                group_size,
                rng,
                swap_steps,
            )
            bad = (counts >= majority).sum(axis=0)
            key = (int(bad.sum()), int(bad.max()), tuple(int(value) for value in bad))
            if best is None or key < best[0]:
                best = (key, groups, counts, bad)
            if np.array_equal(bad, lower_bound):
                break

        assert best is not None
        _, groups, _, bad = best
        flattened = [cover for group in groups for cover in group]
        if len(flattened) != len(indices) or len(set(flattened)) != len(indices):
            raise RuntimeError("group bank does not partition its bucket exactly")
        if set(flattened) != set(int(index) for index in indices):
            raise RuntimeError("group bank changed bucket membership")

        banks[label] = tuple(tuple(int(index) for index in group) for group in groups)
        diagnostics.append(
            GroupBankDiagnostics(
                label=label,
                covers=len(indices),
                groups=group_count,
                group_size=group_size,
                bad_groups_by_attack=tuple(int(value) for value in bad),
                lower_bound_by_attack=tuple(int(value) for value in lower_bound),
            )
        )

    return banks, tuple(diagnostics)
