import numpy as np
import pytest

from narcis.index import CoverIndex, NeuralCodebook
from narcis.protocol import NarcisProtocol, keyed_permutation


def abundant_index(codebook_size: int, per_cluster: int = 100) -> CoverIndex:
    paths = [
        f"cluster_{label}/image_{index}.png"
        for label in range(codebook_size)
        for index in range(per_cluster)
    ]
    labels = np.array(
        [label for label in range(codebook_size) for _ in range(per_cluster)]
    )
    return CoverIndex.build(paths, labels)


def test_protocol_roundtrip_from_received_neural_labels():
    index = abundant_index(16)
    protocol = NarcisProtocol(
        index, 16, b"shared research key", repetition=3
    )
    transmission = protocol.encode(b"hello")
    labels = [index.labels[path] for path in transmission.covers]
    decoded, corrections = protocol.decode_labels(
        labels, transmission.padding_bits
    )
    assert decoded == b"hello"
    assert corrections == 0
    assert len(transmission.covers) == len(set(transmission.covers))
    assert transmission.repetition == 3


def test_repetition_corrects_one_symbol_error_per_group():
    index = abundant_index(16)
    protocol = NarcisProtocol(index, 16, b"shared key", repetition=3)
    transmission = protocol.encode(b"robust")
    labels = [index.labels[path] for path in transmission.covers]
    for offset in range(0, len(labels), 3):
        labels[offset] = (labels[offset] + 1) % 16
    decoded, _ = protocol.decode_labels(labels, transmission.padding_bits)
    assert decoded == b"robust"


def test_protocol_reed_solomon_roundtrip():
    index = abundant_index(16, per_cluster=200)
    protocol = NarcisProtocol(
        index,
        16,
        b"rs key",
        fec="reed_solomon",
        rs_parity=16,
    )
    transmission = protocol.encode(b"reed-solomon")
    labels = [index.labels[path] for path in transmission.covers]
    decoded, _ = protocol.decode_labels(labels, transmission.padding_bits)
    assert decoded == b"reed-solomon"


def test_protocol_reports_insufficient_cover_multiplicity():
    protocol = NarcisProtocol(abundant_index(2, per_cluster=1), 2, b"k")
    feasible, deficits = protocol.feasibility(
        b"a payload longer than two symbols"
    )
    assert not feasible
    assert deficits
    with pytest.raises(ValueError, match="Insufficient"):
        protocol.encode(b"a payload longer than two symbols")


def test_key_changes_symbol_permutation():
    assert keyed_permutation(16, b"first") != keyed_permutation(16, b"second")


def test_keyed_mapping_preserves_gray_locality():
    permutation = keyed_permutation(16, b"locality")
    inverse = {cluster: symbol for symbol, cluster in enumerate(permutation)}
    ordered_clusters = sorted(inverse)
    distances = []
    for first, second in zip(ordered_clusters, ordered_clusters[1:]):
        xor = inverse[first] ^ inverse[second]
        distances.append(xor.bit_count())
    assert sum(distance == 1 for distance in distances) >= 14


def test_cover_selection_is_deterministic_for_same_payload():
    index = abundant_index(16, per_cluster=200)
    protocol = NarcisProtocol(index, 16, b"selection-key")
    first = protocol.encode(b"same protected payload").covers
    second = protocol.encode(b"same protected payload").covers
    assert first == second


def test_cover_selection_diversifies_distinct_payloads():
    index = abundant_index(16, per_cluster=500)
    protocol = NarcisProtocol(index, 16, b"selection-key")
    first = protocol.encode(b"protected payload A").covers
    second = protocol.encode(b"protected payload B").covers
    assert first != second
    overlap = len(set(first).intersection(second))
    assert overlap < min(len(first), len(second))


def test_cover_index_accepts_positive_selection_weights():
    paths = ["a.png", "b.png"]
    labels = np.array([0, 0])
    index = CoverIndex.build(paths, labels, weights=np.array([3.0, 0.5]))
    assert index.selection_weight("a.png") == pytest.approx(3.0)
    assert index.selection_weight("b.png") == pytest.approx(0.5)
    assert index.selection_weight("unknown.png") == pytest.approx(1.0)


def test_cover_index_rejects_nonpositive_weights():
    with pytest.raises(ValueError, match="finite and positive"):
        CoverIndex.build(
            ["a.png"],
            np.array([0]),
            weights=np.array([0.0]),
        )


def test_codebook_predicts_nearest_centroid():
    codebook = NeuralCodebook(np.array([[1.0, 0.0], [0.0, 1.0]]))
    labels = codebook.predict(np.array([[0.9, 0.1], [0.1, 0.9]]))
    assert labels.tolist() == [0, 1]
