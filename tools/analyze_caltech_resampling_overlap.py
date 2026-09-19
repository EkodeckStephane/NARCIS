from __future__ import annotations

from argparse import ArgumentParser
from itertools import combinations
import json
from pathlib import Path

import numpy as np


DEFAULT_SEEDS = (11, 29, 47, 71, 101)


def analyze(source_images: int = 9144, train_images: int = 1500, index_images: int = 7000, seeds=DEFAULT_SEEDS) -> dict:
    indexes = {}
    trains = {}
    for seed in seeds:
        order = np.random.default_rng(seed).permutation(source_images)
        trains[seed] = set(int(v) for v in order[:train_images])
        indexes[seed] = set(int(v) for v in order[train_images : train_images + index_images])

    pairs = []
    for a, b in combinations(seeds, 2):
        overlap = len(indexes[a] & indexes[b])
        pairs.append(
            {
                "seed_a": a,
                "seed_b": b,
                "images": overlap,
                "fraction_of_index": overlap / index_images,
                "train_a_in_index_b": len(trains[a] & indexes[b]),
                "train_b_in_index_a": len(trains[b] & indexes[a]),
            }
        )

    return {
        "status": "descriptive_resampling_overlap",
        "source_images": source_images,
        "train_images_per_run": train_images,
        "index_images_per_run": index_images,
        "seeds": list(seeds),
        "within_run_train_index_disjoint": all(not (trains[s] & indexes[s]) for s in seeds),
        "cross_seed_independence": False,
        "pairwise_index_overlap": pairs,
        "all_five_index_intersection_images": len(set.intersection(*(indexes[s] for s in seeds))),
        "reporting_rule": (
            "The five runs are seeded train-index resamplings of one external corpus. "
            "They quantify sensitivity to data assignment and are not treated as independent external replications."
        ),
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("tomm_results/caltech_resampling_overlap.json"))
    args = parser.parse_args()
    result = analyze()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
