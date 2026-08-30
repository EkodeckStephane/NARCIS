import numpy as np

from narcis.group_bank_protocol import (
    encode_group_bank,
    majority_failure_signatures,
)
from narcis.index import CoverIndex
from narcis.protocol import NarcisProtocol


def test_group_bank_protocol_roundtrip_and_no_reuse():
    codebook_size = 4
    groups_per_label = 40
    group_size = 5
    identifiers = [
        f"label-{label}/cover-{offset}.png"
        for label in range(codebook_size)
        for offset in range(groups_per_label * group_size)
    ]
    labels = np.asarray(
        [
            label
            for label in range(codebook_size)
            for _ in range(groups_per_label * group_size)
        ]
    )
    index = CoverIndex.build(identifiers, labels)
    banks = {}
    for label in range(codebook_size):
        positions = np.flatnonzero(labels == label)
        banks[label] = tuple(
            tuple(int(value) for value in positions[start : start + group_size])
            for start in range(0, len(positions), group_size)
        )
    correct = np.ones((len(identifiers), 3), dtype=bool)
    signatures = majority_failure_signatures(banks, correct)
    protocol = NarcisProtocol(
        index,
        codebook_size,
        b"group-bank-secret",
        repetition=5,
        fec="hamming",
    )
    transmission = encode_group_bank(
        protocol,
        b"A",
        sequence=7,
        identifiers=identifiers,
        banks=banks,
        signatures=signatures,
    )
    received = [index.labels[path] for path in transmission.covers]
    recovered, corrections = protocol.decode_labels(
        received,
        transmission.padding_bits,
        sequence=7,
    )
    assert recovered == b"A"
    assert corrections == 0
    assert len(transmission.covers) == len(set(transmission.covers))
    assert transmission.repetition == 5


def test_majority_failure_signatures_encode_group_failure():
    banks = {0: ((0, 1, 2, 3, 4), (5, 6, 7, 8, 9))}
    correct = np.ones((10, 2), dtype=bool)
    correct[[0, 1, 2], 0] = False
    correct[[5, 6], 1] = False
    signatures = majority_failure_signatures(banks, correct)
    # First group fails attack 0 by majority; second has only two failures.
    assert signatures[0].tolist() == [1, 0]
