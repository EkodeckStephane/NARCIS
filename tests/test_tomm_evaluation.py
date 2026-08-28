import numpy as np
import pandas as pd

from narcis.tomm_evaluation import (
    select_calibration_locked_projection,
    summarize_payload_trials,
)


def test_projection_selection_uses_calibration_inputs_and_builds_weighted_index():
    rng = np.random.default_rng(20260828)
    clean = rng.normal(size=(512, 8))
    clean /= np.maximum(np.linalg.norm(clean, axis=1, keepdims=True), 1e-12)
    attacked = {
        "small_noise": clean + rng.normal(scale=0.002, size=clean.shape),
        "shift": clean + rng.normal(scale=0.003, size=clean.shape),
    }
    visual = rng.normal(size=(512, 7))
    identifiers = [f"image_{index}.png" for index in range(len(clean))]

    choice, candidates = select_calibration_locked_projection(
        clean,
        attacked,
        identifiers,
        visual,
        clusters=4,
        principal_components=4,
        random_directions=4,
        random_seed=17,
    )

    assert len(candidates) == 8
    assert choice.codebook.size == 4
    assert choice.name in set(candidates["direction"])
    assert set(choice.index.labels).issubset(set(identifiers))
    assert set(choice.index.weights) == set(choice.index.labels)
    assert choice.index.minimum_bucket_size(4) > 0


def test_payload_summary_aggregates_success_and_accuracy():
    raw = pd.DataFrame(
        [
            {
                "dataset": "demo",
                "seed": 11,
                "payload_bytes": 32,
                "attack": "jpeg",
                "message_success": 1,
                "symbol_accuracy": 0.99,
                "covers": 100,
                "rs_corrections": 2,
            },
            {
                "dataset": "demo",
                "seed": 11,
                "payload_bytes": 32,
                "attack": "jpeg",
                "message_success": 1,
                "symbol_accuracy": 0.97,
                "covers": 100,
                "rs_corrections": 3,
            },
            {
                "dataset": "demo",
                "seed": 11,
                "payload_bytes": 32,
                "attack": "preflight",
                "message_success": 0,
                "symbol_accuracy": np.nan,
                "covers": 0,
                "rs_corrections": -1,
            },
        ]
    )
    summary = summarize_payload_trials(raw)
    assert len(summary) == 1
    row = summary.iloc[0]
    assert row["trials"] == 2
    assert row["successes"] == 2
    assert row["message_success"] == 1.0
    assert row["mean_symbol_accuracy"] == 0.98
    assert row["maximum_rs_corrections"] == 3
