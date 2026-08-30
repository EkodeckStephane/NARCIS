from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from narcis.benchmark import (
    benchmark_master_key,
    benchmark_nonce,
    benchmark_workload,
    derive_subkey,
)
from narcis.security import PAYLOAD_ID


def test_benchmark_workload_has_global_sequences_and_unique_nonces():
    master, encryption_key, messages = benchmark_workload("BOSSBase", 11)
    assert len(master) == 32
    assert len(encryption_key) == 32
    assert len(messages) == 30
    assert [message.sequence for message in messages] == list(range(30))
    assert [message.payload_bytes for message in messages] == [8] * 10 + [32] * 10 + [64] * 10
    assert len({message.envelope[:12] for message in messages}) == 30


def test_benchmark_workload_is_exactly_reproducible():
    first = benchmark_workload("Caltech-101", 47)
    second = benchmark_workload("Caltech-101", 47)
    assert first == second
    assert benchmark_master_key("Caltech-101", 47) != benchmark_master_key("Caltech-101", 71)


def test_benchmark_envelopes_authenticate_with_global_sequence():
    master, encryption_key, messages = benchmark_workload("demo", 29)
    assert derive_subkey(master, b"payload-encryption") == encryption_key
    for message in messages:
        nonce = message.envelope[:12]
        ciphertext = message.envelope[12:]
        associated = PAYLOAD_ID + message.sequence.to_bytes(8, "big")
        recovered = AESGCM(encryption_key).decrypt(nonce, ciphertext, associated)
        assert recovered == message.plaintext
        assert nonce == benchmark_nonce(master, message.sequence)
