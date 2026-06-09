import pytest

from narcis.coding import (
    bits_to_symbols,
    decode_payload,
    decode_payload_rs,
    encode_payload,
    encode_payload_rs,
    hamming74_decode,
    hamming74_encode,
    symbols_to_bits,
)


def test_hamming_corrects_every_single_bit_error():
    data = [1, 0, 1, 1]
    encoded = hamming74_encode(data)
    for index in range(7):
        damaged = encoded.copy()
        damaged[index] ^= 1
        decoded, corrected = hamming74_decode(damaged)
        assert decoded == data
        assert corrected


def test_payload_roundtrip_and_crc():
    encoded = encode_payload(b"NARCIS")
    decoded, corrections = decode_payload(encoded)
    assert decoded == b"NARCIS"
    assert corrections == 0


def test_symbol_pack_roundtrip():
    bits = encode_payload(b"coverless")
    symbols, padding = bits_to_symbols(bits, 4)
    assert symbols_to_bits(symbols, 4, padding) == bits


def test_crc_rejects_uncorrectable_corruption():
    encoded = encode_payload(b"integrity")
    encoded[2] ^= 1
    encoded[4] ^= 1
    with pytest.raises(ValueError, match="CRC|Invalid"):
        decode_payload(encoded)


def test_reed_solomon_corrects_byte_errors():
    encoded = encode_payload_rs(b"burst errors", parity_bytes=16)
    for byte_index in (2, 5, 9, 12):
        encoded[byte_index * 8] ^= 1
    decoded, corrections = decode_payload_rs(encoded, parity_bytes=16)
    assert decoded == b"burst errors"
    assert corrections == 4
