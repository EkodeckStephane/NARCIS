import numpy as np

from narcis.glcm import (
    glcm_matrix,
    glcm_texture_complexity,
    glcm_texture_features,
)


def test_glcm_is_normalized_and_symmetric():
    image = np.array(
        [
            [0.0, 0.0, 1.0, 1.0],
            [0.0, 0.0, 1.0, 1.0],
            [1.0, 1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0, 0.0],
        ]
    )
    matrix = glcm_matrix(image, (0, 1), levels=8)
    assert np.isclose(matrix.sum(), 1.0)
    assert np.allclose(matrix, matrix.T)


def test_texture_features_are_finite():
    rng = np.random.default_rng(20260828)
    image = rng.random((64, 64))
    features = glcm_texture_features(image)
    assert features.shape == (5,)
    assert np.all(np.isfinite(features))


def test_checkerboard_has_more_complexity_than_constant_image():
    constant = np.full((64, 64), 0.5)
    checkerboard = (np.indices((64, 64)).sum(axis=0) % 2).astype(float)
    assert glcm_texture_complexity(checkerboard) > glcm_texture_complexity(constant)


def test_rgb_channel_first_input_is_supported():
    image = np.stack(
        [
            np.zeros((32, 32)),
            np.ones((32, 32)),
            np.eye(32),
        ]
    )
    value = glcm_texture_complexity(image)
    assert np.isfinite(value)
