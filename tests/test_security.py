import os

import pytest
from cryptography.exceptions import InvalidTag

from narcis.security import (
    ReplayGuard,
    SessionMetadata,
    decrypt_payload,
    encrypt_payload,
    open_metadata,
    seal_metadata,
)


def test_metadata_authentication_and_replay_rejection():
    key = os.urandom(32)
    metadata = SessionMetadata(1, 2, 8, 75)
    envelope = seal_metadata(metadata, key, "alice", "bob")
    guard = ReplayGuard()
    assert open_metadata(envelope, key, "alice", "bob", guard) == metadata
    with pytest.raises(ValueError, match="Replay"):
        open_metadata(envelope, key, "alice", "bob", guard)


def test_metadata_tampering_is_detected():
    key = os.urandom(32)
    envelope = bytearray(
        seal_metadata(SessionMetadata(2, 1, 8, 20), key, "alice", "bob")
    )
    envelope[-1] ^= 1
    with pytest.raises(InvalidTag):
        open_metadata(
            bytes(envelope), key, "alice", "bob", ReplayGuard()
        )


def test_payload_encryption_roundtrip_and_sequence_binding():
    key = os.urandom(32)
    envelope = encrypt_payload(b"confidential", key, sequence=9)
    assert decrypt_payload(envelope, key, sequence=9) == b"confidential"
    with pytest.raises(InvalidTag):
        decrypt_payload(envelope, key, sequence=10)


def test_benchmark_control_plane_roundtrip_and_negative_checks():
    from narcis.benchmark import benchmark_workload, derive_subkey

    master_key, _, workload = benchmark_workload("Caltech-101", 11)
    metadata_key = derive_subkey(master_key, b"metadata-aead")
    message = workload[0]
    metadata = SessionMetadata(
        sequence=message.sequence,
        padding_bits=2,
        codebook_size=8,
        cover_count=2320,
    )
    envelope = seal_metadata(metadata, metadata_key, "arcis-sender", "arcis-receiver")
    guard = ReplayGuard()
    assert open_metadata(
        envelope,
        metadata_key,
        "arcis-sender",
        "arcis-receiver",
        guard,
    ) == metadata
    with pytest.raises(ValueError, match="Replay"):
        open_metadata(
            envelope,
            metadata_key,
            "arcis-sender",
            "arcis-receiver",
            guard,
        )
    tampered = bytearray(envelope)
    tampered[-1] ^= 1
    with pytest.raises(InvalidTag):
        open_metadata(
            bytes(tampered),
            metadata_key,
            "arcis-sender",
            "arcis-receiver",
            ReplayGuard(),
        )
