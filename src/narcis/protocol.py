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


def keyed_permutation(
    size: int,
    key: bytes,
    sequence: int | None = None,
) -> list[int]:
    """Return a keyed Gray permutation with exact cyclic session balancing.

    ``key`` is the mapping subkey. A secret base rotation and a secret fixed
    orientation are derived from it. The authenticated session sequence then
    advances the rotation by one position modulo ``size``. Consequently, for
    every fixed Gray symbol, any ``size`` consecutive session sequences visit
    every cluster exactly once while Gray locality is preserved in every
    individual session.
    """
    if size < 2 or size & (size - 1):
        raise ValueError("Codebook size must be a power of two")
    sequence = 0 if sequence is None else int(sequence)
    if sequence < 0:
        raise ValueError("sequence must be non-negative")

    base_digest = hmac.new(key, b"mapping-base", hashlib.sha256).digest()
    base_shift = int.from_bytes(base_digest[:8], "big") % size
    shift = (base_shift + sequence) % size
    orientation = hmac.new(key, b"mapping-orientation", hashlib.sha256).digest()
    reverse = bool(orientation[0] & 1)

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
        self.mapping_key = hmac.new(
            key, b"cluster-mapping", hashlib.sha256
        ).digest()
        self.selection_key = hmac.new(
            key, b"cover-selection", hashlib.sha256
        ).digest()
        # Compatibility snapshots for callers that inspect these attributes.
        self.permutation = self._permutation(0)
        self.inverse = {
            cluster: symbol for symbol, cluster in enumerate(self.permutation)
        }

    def _permutation(self, sequence: int) -> list[int]:
        return keyed_permutation(
            self.codebook_size,
            self.mapping_key,
            sequence=sequence,
        )

    def demand(
        self,
        payload: bytes,
        sequence: int = 0,
    ) -> tuple[dict[int, int], int]:
        coded = (
            encode_payload(payload)
            if self.fec == "hamming"
            else encode_payload_rs(payload, self.rs_parity)
        )
        symbols, padding = bits_to_symbols(
            coded, self.bits_per_symbol
        )
        permutation = self._permutation(sequence)
        required = Counter(
            permutation[symbol]
            for symbol in symbols
            for _ in range(self.repetition)
        )
        return dict(required), padding

    def feasibility(
        self,
        payload: bytes,
        sequence: int = 0,
    ) -> tuple[bool, dict[int, int]]:
        required, _ = self.demand(payload, sequence=sequence)
        deficits = {
            cluster: count - len(self.cover_index.buckets.get(cluster, []))
            for cluster, count in required.items()
            if count > len(self.cover_index.buckets.get(cluster, []))
        }
        return not deficits, deficits

    def _selection_context(self, payload: bytes, sequence: int) -> bytes:
        return hmac.new(
            self.selection_key,
            b"sequence:"
            + int(sequence).to_bytes(8, "big", signed=False)
            + b":payload:"
            + hashlib.sha256(payload).digest(),
            hashlib.sha256,
        ).digest()

    def _weighted_cover_order(
        self,
        cluster: int,
        payload_context: bytes,
    ) -> list[str]:
        candidates = self.cover_index.buckets.get(cluster, [])
        ranked: list[tuple[float, bytes, str]] = []
        cluster_bytes = int(cluster).to_bytes(4, "big", signed=False)
        for path in candidates:
            digest = hmac.new(
                self.selection_key,
                b"candidate:" + payload_context + cluster_bytes + path.encode("utf-8"),
                hashlib.sha256,
            ).digest()
            integer = int.from_bytes(digest[:8], "big")
            uniform = (integer + 1.0) / (2**64 + 1.0)
            weight = max(self.cover_index.selection_weight(path), 1e-12)
            score = -math.log(uniform) / weight
            ranked.append((score, digest, path))
        ranked.sort(key=lambda row: (row[0], row[1], row[2]))
        return [path for _, _, path in ranked]

    def encode(self, payload: bytes, sequence: int = 0) -> Transmission:
        coded = (
            encode_payload(payload)
            if self.fec == "hamming"
            else encode_payload_rs(payload, self.rs_parity)
        )
        symbols, padding = bits_to_symbols(
            coded, self.bits_per_symbol
        )
        permutation = self._permutation(sequence)
        required_clusters = {
            permutation[symbol] for symbol in symbols
        }
        payload_context = self._selection_context(payload, sequence)
        ordered_candidates = {
            cluster: self._weighted_cover_order(cluster, payload_context)
            for cluster in required_clusters
        }
        cursors = {label: 0 for label in range(self.codebook_size)}
        covers: list[str] = []
        for symbol in symbols:
            cluster = permutation[symbol]
            for _ in range(self.repetition):
                candidates = ordered_candidates[cluster]
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
        self,
        received_labels: list[int],
        padding_bits: int,
        sequence: int = 0,
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
        permutation = self._permutation(sequence)
        inverse = {
            cluster: symbol for symbol, cluster in enumerate(permutation)
        }
        try:
            symbols = [inverse[label] for label in received_labels]
        except KeyError as error:
            raise ValueError(f"Unknown received cluster {error.args[0]}") from error
        coded_bits = symbols_to_bits(
            symbols, self.bits_per_symbol, padding_bits
        )
        if self.fec == "hamming":
            return decode_payload(coded_bits)
        return decode_payload_rs(coded_bits, self.rs_parity)
