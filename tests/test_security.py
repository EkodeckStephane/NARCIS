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
