from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import hmac

import numpy as np

from .coding import bits_to_symbols, encode_payload, encode_payload_rs
from .protocol import NarcisProtocol, Transmission


def majority_failure_signatures(
    banks: dict[int, tuple[tuple[int, ...], ...]],
    correct: np.ndarray,
) -> dict[int, np.ndarray]:
    """Encode each group's calibration majority-failure pattern as a bitmask."""
    correct = np.asarray(correct, dtype=bool)
    if correct.ndim != 2:
        raise ValueError("correct must be a cover-by-attack matrix")
    if correct.shape[1] > 63:
        raise ValueError("at most 63 calibration attacks are supported")
    signatures: dict[int, np.ndarray] = {}
    for label, groups in banks.items():
        values = []
        for group in groups:
            positions = np.asarray(group, dtype=int)
            if len(positions) < 3 or len(positions) % 2 == 0:
                raise ValueError("group banks must contain odd groups of size at least three")
            majority = len(positions) // 2 + 1
            failures = (~correct[positions]).sum(axis=0) >= majority
            signature = 0
            for attack, failed in enumerate(failures):
                signature |= int(bool(failed)) << attack
            values.append(signature)
        signatures[int(label)] = np.asarray(values, dtype=np.uint64)
    return signatures


def _ordered_group_indices(
    groups: tuple[tuple[int, ...], ...],
    signatures: np.ndarray,
    identifiers: list[str],
    selection_key: bytes,
    context: bytes,
    label: int,
    demand: int,
) -> list[int]:
    if len(groups) != len(signatures):
        raise ValueError("groups and signatures must align")
    if demand > len(groups):
        raise ValueError(f"group capacity exhausted for label {label}")

    label_bytes = int(label).to_bytes(4, "big", signed=False)
    by_signature: dict[int, list[tuple[bytes, int]]] = defaultdict(list)
    for group_index, group in enumerate(groups):
        signature = int(signatures[group_index])
        membership = b"|".join(
            identifiers[position].encode("utf-8") for position in sorted(group)
        )
        digest = hmac.new(
            selection_key,
            b"group:"
            + context
            + label_bytes
            + signature.to_bytes(8, "big", signed=False)
            + membership,
            hashlib.sha256,
        ).digest()
        by_signature[signature].append((digest, group_index))
    for signature in by_signature:
        by_signature[signature].sort()

    proportions = {
        signature: len(rows) / len(groups)
        for signature, rows in by_signature.items()
    }
    used = Counter()
    cursors = Counter()
    ordered: list[int] = []
    for step in range(demand):
        available = [
            signature
            for signature, rows in by_signature.items()
            if cursors[signature] < len(rows)
        ]
        signature = min(
            available,
            key=lambda value: (
                -(proportions[value] * (step + 1) - used[value]),
                hmac.new(
                    selection_key,
                    b"signature:"
                    + context
                    + label_bytes
                    + int(value).to_bytes(8, "big", signed=False),
                    hashlib.sha256,
                ).digest(),
                value,
            ),
        )
        ordered.append(by_signature[signature][cursors[signature]][1])
        cursors[signature] += 1
        used[signature] += 1
    return ordered


def encode_group_bank(
    protocol: NarcisProtocol,
    payload: bytes,
    sequence: int,
    identifiers: list[str],
    banks: dict[int, tuple[tuple[int, ...], ...]],
    signatures: dict[int, np.ndarray],
) -> Transmission:
    """Encode one protected payload using the frozen balanced group-bank rule."""
    if protocol.repetition < 3 or protocol.repetition % 2 == 0:
        raise ValueError("group-bank selection requires an odd repetition >= 3")

    coded = (
        encode_payload(payload)
        if protocol.fec == "hamming"
        else encode_payload_rs(payload, protocol.rs_parity)
    )
    symbols, padding = bits_to_symbols(coded, protocol.bits_per_symbol)
    permutation = protocol._permutation(sequence)
    labels = [permutation[symbol] for symbol in symbols]
    demand = Counter(labels)
    context = protocol._selection_context(payload, sequence)

    orders = {
        label: _ordered_group_indices(
            banks[label],
            signatures[label],
            identifiers,
            protocol.selection_key,
            context,
            label,
            demand[label],
        )
        for label in demand
    }
    cursors = Counter()
    selected: list[str] = []
    used_positions: set[int] = set()
    for label in labels:
        group_index = orders[label][cursors[label]]
        cursors[label] += 1
        group = banks[label][group_index]
        if len(group) != protocol.repetition:
            raise ValueError("group size must match protocol repetition")
        members = sorted(
            group,
            key=lambda position: hmac.new(
                protocol.selection_key,
                b"member:"
                + context
                + int(label).to_bytes(4, "big", signed=False)
                + identifiers[position].encode("utf-8"),
                hashlib.sha256,
            ).digest(),
        )
        for position in members:
            if position in used_positions:
                raise RuntimeError("cover reuse detected within a transmission")
            used_positions.add(position)
            selected.append(identifiers[position])

    return Transmission(
        covers=selected,
        padding_bits=padding,
        codebook_size=protocol.codebook_size,
        repetition=protocol.repetition,
        fec=protocol.fec,
    )
