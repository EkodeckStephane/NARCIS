import numpy as np
import pytest

from narcis.index import QuantileCodebook


def test_quantile_codebook_accepts_an_explicit_direction():
    embeddings = np.array(
        [[-2.0, 3.0], [-1.0, 2.0], [1.0, 1.0], [2.0, 0.0]],
        dtype=np.float32,
    )
    codebook = QuantileCodebook.fit_direction(
        embeddings,
        clusters=2,
        direction=np.array([2.0, 0.0]),
    )
    assert np.allclose(codebook.direction, [1.0, 0.0])
    assert codebook.predict(embeddings).tolist() == [0, 0, 1, 1]


def test_quantile_codebook_rejects_an_invalid_direction():
    embeddings = np.ones((4, 2), dtype=np.float32)
    with pytest.raises(ValueError, match="embedding dimension"):
        QuantileCodebook.fit_direction(embeddings, 2, np.ones(3))
    with pytest.raises(ValueError, match="non-zero"):
        QuantileCodebook.fit_direction(embeddings, 2, np.zeros(2))
