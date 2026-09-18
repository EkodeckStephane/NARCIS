from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .security import PAYLOAD_ID


BENCHMARK_ROOT = b"NARCIS-TOMM-BENCHMARK-20260830"


@dataclass(frozen=True)
class BenchmarkMessage:
    sequence: int
    payload_bytes: int
    plaintext: bytes
    envelope: bytes


def derive_subkey(master_key: bytes, label: bytes) -> bytes:
    """Derive one SHA-256-sized benchmark subkey with explicit domain separation."""
    return hmac.new(master_key, label, hashlib.sha256).digest()


def benchmark_master_key(dataset: str, seed: int) -> bytes:
    """Return the public deterministic benchmark key for one dataset partition.

    This function exists for exact experimental reproducibility. Its output is
    intentionally reproducible and must not be presented as production key
    management guidance.
    """
    if seed < 0:
        raise ValueError("seed must be non-negative")
    material = dataset.encode("utf-8") + b":" + int(seed).to_bytes(8, "big")
    return hmac.new(BENCHMARK_ROOT, material, hashlib.sha256).digest()


def deterministic_plaintext(master_key: bytes, sequence: int, length: int) -> bytes:
    if sequence < 0:
        raise ValueError("sequence must be non-negative")
    if length < 0:
        raise ValueError("length must be non-negative")
    output = bytearray()
    counter = 0
    while len(output) < length:
        output.extend(
            hmac.new(
                master_key,
                b"plaintext:"
                + int(sequence).to_bytes(8, "big")
                + int(counter).to_bytes(4, "big"),
                hashlib.sha256,
            ).digest()
        )
        counter += 1
    return bytes(output[:length])


def benchmark_nonce(master_key: bytes, sequence: int) -> bytes:
    """Return a deterministic 96-bit nonce unique for each sequence under a key."""
    if sequence < 0:
        raise ValueError("sequence must be non-negative")
    prefix = derive_subkey(master_key, b"nonce-prefix")[:4]
    return prefix + int(sequence).to_bytes(8, "big")


def benchmark_workload(
    dataset: str,
    seed: int,
    payload_sizes: tuple[int, ...] = (8, 32, 64),
    messages_per_size: int = 10,
) -> tuple[bytes, bytes, tuple[BenchmarkMessage, ...]]:
    """Build the frozen TOMM workload with globally unique session sequences."""
    if messages_per_size < 1:
        raise ValueError("messages_per_size must be positive")
    master_key = benchmark_master_key(dataset, seed)
    encryption_key = derive_subkey(master_key, b"payload-encryption")
    messages: list[BenchmarkMessage] = []
    sequence = 0
    for payload_bytes in payload_sizes:
        if payload_bytes < 1:
            raise ValueError("payload sizes must be positive")
        for _ in range(messages_per_size):
            plaintext = deterministic_plaintext(master_key, sequence, payload_bytes)
            nonce = benchmark_nonce(master_key, sequence)
            associated = PAYLOAD_ID + sequence.to_bytes(8, "big")
            envelope = nonce + AESGCM(encryption_key).encrypt(
                nonce,
                plaintext,
                associated,
            )
            messages.append(
                BenchmarkMessage(
                    sequence=sequence,
                    payload_bytes=payload_bytes,
                    plaintext=plaintext,
                    envelope=envelope,
                )
            )
            sequence += 1

    nonces = [message.envelope[:12] for message in messages]
    if len(nonces) != len(set(nonces)):
        raise RuntimeError("benchmark nonce collision detected")
    return master_key, encryption_key, tuple(messages)
