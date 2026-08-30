from __future__ import annotations

from collections import Counter

import numpy as np

from .coding import bits_to_symbols, encode_payload, encode_payload_rs
from .complementary import select_complementary_triplet
from .protocol import NarcisProtocol, Transmission


def encode_complementary(
    protocol: NarcisProtocol,
    payload: bytes,
    sequence: int,
    identifiers: list[str],
    failure_masks: np.ndarray,
    strata: np.ndarray,
) -> Transmission:
    """Encode one payload with distribution-matched complementary triplets.

    This function deliberately delegates the keyed symbol mapping and
    selection-context derivation to ``NarcisProtocol``. It replaces only the
    within-label cover selection rule. The protocol must use repetition three;
    triplet majority is the mathematical basis of this selection strategy.
    """
    if protocol.repetition != 3:
        raise ValueError("complementary selection requires repetition three")
    if len(identifiers) != len(failure_masks) or len(identifiers) != len(strata):
        raise ValueError("identifiers, failure masks, and strata must align")

    coded = (
        encode_payload(payload)
        if protocol.fec == "hamming"
        else encode_payload_rs(payload, protocol.rs_parity)
    )
    symbols, padding = bits_to_symbols(coded, protocol.bits_per_symbol)
    permutation = protocol._permutation(sequence)
    payload_context = protocol._selection_context(payload, sequence)

    position_by_identifier = {
        identifier: position for position, identifier in enumerate(identifiers)
    }
    positions_by_label = {
        label: np.asarray(
            [
                position_by_identifier[identifier]
                for identifier in protocol.cover_index.buckets.get(label, [])
            ],
            dtype=int,
        )
        for label in range(protocol.codebook_size)
    }

    used_positions: set[int] = set()
    stratum_used = {
        label: Counter() for label in range(protocol.codebook_size)
    }
    selected_identifiers: list[str] = []

    for symbol in symbols:
        label = permutation[symbol]
        triplet = select_complementary_triplet(
            candidate_positions=positions_by_label[label],
            failure_masks=failure_masks,
            strata=strata,
            identifiers=identifiers,
            codebook_label=label,
            selection_key=protocol.selection_key,
            context=payload_context,
            used_positions=used_positions,
            stratum_used=stratum_used[label],
        )
        for position in triplet:
            used_positions.add(position)
            stratum_used[label][int(strata[position])] += 1
            selected_identifiers.append(identifiers[position])

    return Transmission(
        covers=selected_identifiers,
        padding_bits=padding,
        codebook_size=protocol.codebook_size,
        repetition=3,
        fec=protocol.fec,
    )
