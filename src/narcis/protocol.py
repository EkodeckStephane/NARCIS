from dataclasses import dataclass
from collections import Counter
import hashlib
import hmac
import math

from .coding import (
    bits_to_symbols,
    decode_payload,
    decode_payload_rs,
    encode_payload,
    encode_payload_rs,
    symbols_to_bits,
)
from .index import CoverIndex


def keyed_permutation(size: int, key: bytes) -> list[int]:
    if size < 2 or size & (size - 1):
        raise ValueError("Codebook size must be a power of two")
    digest = hmac.new(key, b"cluster-order", hashlib.sha256).digest()
    shift = int.from_bytes(digest[:8], "big") % size
    reverse = bool(digest[8] & 1)
    permutation = [0] * size
    for position in range(size):
        gray_symbol = position ^ (position >> 1)
        oriented = -position if reverse else position
        permutation[gray_symbol] = (shift + oriented) % size
    return permutation


@dataclass(frozen=True)
class Transmission:
    covers: list[str]
    padding_bits: int
    codebook_size: int
    repetition: int
    fec: str


class NarcisProtocol:
    def __init__(
        self,
        cover_index: CoverIndex,
        codebook_size: int,
        key: bytes,
        repetition: int = 1,
        fec: str = "hamming",
        rs_parity: int = 64,
    ):
        self.cover_index = cover_index
        self.codebook_size = codebook_size
        if repetition < 1 or repetition % 2 == 0:
            raise ValueError("repetition must be a positive odd integer")
        self.repetition = repetition
        if fec not in {"hamming", "reed_solomon"}:
            raise ValueError("fec must be hamming or reed_solomon")
        self.fec = fec
        self.rs_parity = rs_parity
        self.bits_per_symbol = int(math.log2(codebook_size))
        if 2**self.bits_per_symbol != codebook_size:
            raise ValueError("codebook_size must be a power of two")
        self.permutation = keyed_permutation(codebook_size, key)
        self.inverse = {
            cluster: symbol for symbol, cluster in enumerate(self.permutation)
        }

    def demand(self, payload: bytes) -> tuple[dict[int, int], int]:
        coded = (
            encode_payload(payload)
            if self.fec == "hamming"
            else encode_payload_rs(payload, self.rs_parity)
        )
        symbols, padding = bits_to_symbols(
            coded, self.bits_per_symbol
        )
        required = Counter(
            self.permutation[symbol]
            for symbol in symbols
            for _ in range(self.repetition)
        )
        return dict(required), padding

    def feasibility(self, payload: bytes) -> tuple[bool, dict[int, int]]:
        required, _ = self.demand(payload)
        deficits = {
            cluster: count - len(self.cover_index.buckets.get(cluster, []))
            for cluster, count in required.items()
            if count > len(self.cover_index.buckets.get(cluster, []))
        }
        return not deficits, deficits

    def encode(self, payload: bytes) -> Transmission:
        coded = (
            encode_payload(payload)
            if self.fec == "hamming"
            else encode_payload_rs(payload, self.rs_parity)
        )
        symbols, padding = bits_to_symbols(
            coded, self.bits_per_symbol
        )
        cursors = {label: 0 for label in range(self.codebook_size)}
        covers: list[str] = []
        for symbol in symbols:
            cluster = self.permutation[symbol]
            for _ in range(self.repetition):
                candidates = self.cover_index.buckets.get(cluster, [])
                cursor = cursors[cluster]
                if cursor >= len(candidates):
                    raise ValueError(
                        f"Insufficient unused covers for cluster {cluster}: "
                        f"need at least {cursor + 1}"
                    )
                covers.append(candidates[cursor])
                cursors[cluster] += 1
        return Transmission(
            covers,
            padding,
            self.codebook_size,
            self.repetition,
            self.fec,
        )

    def decode_labels(
        self, received_labels: list[int], padding_bits: int
    ) -> tuple[bytes, int]:
        if len(received_labels) % self.repetition:
            raise ValueError("Received label count violates repetition framing")
        if self.repetition > 1:
            voted = []
            for index in range(0, len(received_labels), self.repetition):
                group = received_labels[index : index + self.repetition]
                counts = Counter(group)
                voted.append(
                    max(counts, key=lambda label: (counts[label], -label))
                )
            received_labels = voted
        try:
            symbols = [self.inverse[label] for label in received_labels]
        except KeyError as error:
            raise ValueError(f"Unknown received cluster {error.args[0]}") from error
        coded_bits = symbols_to_bits(
            symbols, self.bits_per_symbol, padding_bits
        )
        if self.fec == "hamming":
            return decode_payload(coded_bits)
        return decode_payload_rs(coded_bits, self.rs_parity)
