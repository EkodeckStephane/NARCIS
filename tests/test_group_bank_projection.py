import numpy as np

from narcis.group_bank_projection import select_group_bank_projection


def test_group_bank_projection_uses_only_calibration_inputs():
    rng = np.random.default_rng(20260830)
    clean = rng.normal(size=(400, 8))
    clean /= np.maximum(np.linalg.norm(clean, axis=1, keepdims=True), 1e-12)
    attacked = {
        "calibration_a": clean + rng.normal(scale=0.001, size=clean.shape),
        "calibration_b": clean + rng.normal(scale=0.002, size=clean.shape),
    }
    visual = rng.normal(size=(400, 7))
    choice, candidates = select_group_bank_projection(
        clean,
        attacked,
        visual,
        clusters=4,
        group_size=5,
        principal_components=4,
        random_directions=4,
        random_seed=17,
    )
    assert len(candidates) == 8
    assert choice.codebook.size == 4
    assert choice.name in set(candidates["direction"])
    counts = np.bincount(choice.labels, minlength=4)
    assert counts.tolist() == [100, 100, 100, 100]
    assert np.all(counts % 5 == 0)
    assert choice.calibration_correct.shape == (400, 2)
    assert np.isfinite(choice.max_unavoidable_bad_fraction)
    assert np.isfinite(choice.sum_unavoidable_bad_fraction)


def test_group_bank_projection_rejects_misaligned_calibration_embeddings():
    clean = np.eye(20, 4)[np.arange(20) % 4]
    visual = np.zeros((20, 2))
    attacked = {"bad": np.zeros((19, 4))}
    try:
        select_group_bank_projection(
            clean,
            attacked,
            visual,
            clusters=4,
            group_size=5,
            principal_components=2,
            random_directions=1,
        )
    except ValueError as error:
        assert "does not align" in str(error)
    else:
        raise AssertionError("misaligned calibration embeddings should fail")
