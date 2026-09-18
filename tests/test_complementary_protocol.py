import numpy as np

from narcis.coding import bits_to_symbols, encode_payload
from narcis.complementary_protocol import encode_complementary
from narcis.index import CoverIndex
from narcis.protocol import NarcisProtocol


def test_complementary_protocol_roundtrip_with_clean_labels():
    codebook_size = 4
    payload = b"A"
    symbols, _ = bits_to_symbols(encode_payload(payload), bits_per_symbol=2)
    # Every coded symbol consumes one fresh triplet. Provision each label for
    # the conservative worst case in which all coded symbols map to the same
    # clean label; this keeps the test focused on round-trip correctness rather
    # than accidental finite-index exhaustion.
    per_label = 3 * len(symbols)
    identifiers = [
        f"label-{label}/cover-{index}.png"
        for label in range(codebook_size)
        for index in range(per_label)
    ]
    labels = np.asarray(
        [label for label in range(codebook_size) for _ in range(per_label)]
    )
    index = CoverIndex.build(identifiers, labels)
    protocol = NarcisProtocol(
        index,
        codebook_size,
        b"complementary-secret-key",
        repetition=3,
        fec="hamming",
    )

    # Three complementary failure families are repeated in each clean label.
    pattern = np.asarray([0b001, 0b010, 0b100] * (per_label // 3), dtype=np.uint64)
    failure_masks = np.tile(pattern, codebook_size)
    strata = np.asarray([position % 6 for position in range(len(identifiers))])

    transmission = encode_complementary(
        protocol,
        payload,
        sequence=7,
        identifiers=identifiers,
        failure_masks=failure_masks,
        strata=strata,
    )
    received_labels = [index.labels[path] for path in transmission.covers]
    recovered, corrections = protocol.decode_labels(
        received_labels,
        transmission.padding_bits,
        sequence=7,
    )
    assert recovered == payload
    assert corrections == 0
    assert len(transmission.covers) == len(set(transmission.covers))
