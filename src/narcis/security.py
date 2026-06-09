from dataclasses import dataclass
import json
import os
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


PROTOCOL_ID = b"NARCIS-1"
PAYLOAD_ID = b"NARCIS-PAYLOAD-1"


@dataclass(frozen=True)
class SessionMetadata:
    sequence: int
    padding_bits: int
    codebook_size: int
    cover_count: int


class ReplayGuard:
    def __init__(self):
        self._highest: dict[str, int] = {}

    def accept(self, sender: str, sequence: int) -> None:
        previous = self._highest.get(sender, -1)
        if sequence <= previous:
            raise ValueError("Replay or out-of-order session rejected")
        self._highest[sender] = sequence


def encrypt_payload(
    payload: bytes,
    key: bytes,
    sequence: int,
    nonce: bytes | None = None,
) -> bytes:
    if len(key) not in (16, 24, 32):
        raise ValueError("AES-GCM key must contain 16, 24, or 32 bytes")
    nonce = os.urandom(12) if nonce is None else nonce
    if len(nonce) != 12:
        raise ValueError("AES-GCM nonce must contain 12 bytes")
    associated = PAYLOAD_ID + sequence.to_bytes(8, "big")
    return nonce + AESGCM(key).encrypt(nonce, payload, associated)


def decrypt_payload(envelope: bytes, key: bytes, sequence: int) -> bytes:
    if len(envelope) < 28:
        raise ValueError("Truncated encrypted payload")
    nonce, ciphertext = envelope[:12], envelope[12:]
    associated = PAYLOAD_ID + sequence.to_bytes(8, "big")
    return AESGCM(key).decrypt(nonce, ciphertext, associated)


def seal_metadata(
    metadata: SessionMetadata,
    key: bytes,
    sender: str,
    receiver: str,
) -> bytes:
    if len(key) not in (16, 24, 32):
        raise ValueError("AES-GCM key must contain 16, 24, or 32 bytes")
    nonce = os.urandom(12)
    associated = PROTOCOL_ID + sender.encode() + b"\0" + receiver.encode()
    plaintext = json.dumps(
        {
            "sequence": metadata.sequence,
            "padding_bits": metadata.padding_bits,
            "codebook_size": metadata.codebook_size,
            "cover_count": metadata.cover_count,
        },
        separators=(",", ":"),
    ).encode()
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated)
    return struct.pack(">H", len(sender)) + sender.encode() + nonce + ciphertext


def open_metadata(
    envelope: bytes,
    key: bytes,
    expected_sender: str,
    receiver: str,
    replay_guard: ReplayGuard,
) -> SessionMetadata:
    if len(envelope) < 2:
        raise ValueError("Truncated session envelope")
    sender_length = struct.unpack(">H", envelope[:2])[0]
    offset = 2 + sender_length
    if len(envelope) < offset + 13:
        raise ValueError("Truncated session envelope")
    sender = envelope[2:offset].decode()
    if sender != expected_sender:
        raise ValueError("Unexpected sender identity")
    nonce = envelope[offset : offset + 12]
    ciphertext = envelope[offset + 12 :]
    associated = PROTOCOL_ID + sender.encode() + b"\0" + receiver.encode()
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, associated)
    fields = json.loads(plaintext)
    metadata = SessionMetadata(**fields)
    replay_guard.accept(sender, metadata.sequence)
    return metadata
