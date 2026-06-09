import struct
import zlib

from reedsolo import RSCodec, ReedSolomonError


MAGIC = b"NC"


def _bytes_to_bits(data: bytes) -> list[int]:
    return [(byte >> shift) & 1 for byte in data for shift in range(7, -1, -1)]


def _bits_to_bytes(bits: list[int]) -> bytes:
    if len(bits) % 8:
        raise ValueError("Bit length must be divisible by eight")
    return bytes(
        sum(bits[index + offset] << (7 - offset) for offset in range(8))
        for index in range(0, len(bits), 8)
    )


def hamming74_encode(nibble: list[int]) -> list[int]:
    if len(nibble) != 4:
        raise ValueError("Hamming(7,4) expects four data bits")
    d1, d2, d3, d4 = nibble
    p1 = d1 ^ d2 ^ d4
    p2 = d1 ^ d3 ^ d4
    p3 = d2 ^ d3 ^ d4
    return [p1, p2, d1, p3, d2, d3, d4]


def hamming74_decode(codeword: list[int]) -> tuple[list[int], bool]:
    if len(codeword) != 7:
        raise ValueError("Hamming(7,4) expects seven coded bits")
    bits = list(codeword)
    s1 = bits[0] ^ bits[2] ^ bits[4] ^ bits[6]
    s2 = bits[1] ^ bits[2] ^ bits[5] ^ bits[6]
    s3 = bits[3] ^ bits[4] ^ bits[5] ^ bits[6]
    position = s1 + 2 * s2 + 4 * s3
    corrected = position != 0
    if corrected:
        bits[position - 1] ^= 1
    return [bits[2], bits[4], bits[5], bits[6]], corrected


def encode_payload(payload: bytes) -> list[int]:
    frame = MAGIC + struct.pack(">I", len(payload)) + payload
    frame += struct.pack(">I", zlib.crc32(frame) & 0xFFFFFFFF)
    raw_bits = _bytes_to_bits(frame)
    coded: list[int] = []
    for index in range(0, len(raw_bits), 4):
        coded.extend(hamming74_encode(raw_bits[index : index + 4]))
    return coded


def decode_payload(coded_bits: list[int]) -> tuple[bytes, int]:
    if len(coded_bits) % 7:
        raise ValueError("Coded bit length must be divisible by seven")
    raw_bits: list[int] = []
    corrections = 0
    for index in range(0, len(coded_bits), 7):
        nibble, corrected = hamming74_decode(coded_bits[index : index + 7])
        raw_bits.extend(nibble)
        corrections += int(corrected)
    frame = _bits_to_bytes(raw_bits)
    if len(frame) < 10 or frame[:2] != MAGIC:
        raise ValueError("Invalid NARCIS frame")
    payload_length = struct.unpack(">I", frame[2:6])[0]
    end = 6 + payload_length
    if len(frame) < end + 4:
        raise ValueError("Truncated NARCIS frame")
    expected_crc = struct.unpack(">I", frame[end : end + 4])[0]
    if zlib.crc32(frame[:end]) & 0xFFFFFFFF != expected_crc:
        raise ValueError("CRC verification failed")
    return frame[6:end], corrections


def encode_payload_rs(payload: bytes, parity_bytes: int = 64) -> list[int]:
    frame = MAGIC + struct.pack(">I", len(payload)) + payload
    frame += struct.pack(">I", zlib.crc32(frame) & 0xFFFFFFFF)
    encoded = bytes(RSCodec(parity_bytes).encode(frame))
    return _bytes_to_bits(encoded)


def decode_payload_rs(
    coded_bits: list[int], parity_bytes: int = 64
) -> tuple[bytes, int]:
    encoded = _bits_to_bytes(coded_bits)
    try:
        decoded, _, errata = RSCodec(parity_bytes).decode(encoded)
    except ReedSolomonError as error:
        raise ValueError("Reed-Solomon decoding failed") from error
    frame = bytes(decoded)
    if len(frame) < 10 or frame[:2] != MAGIC:
        raise ValueError("Invalid NARCIS frame")
    payload_length = struct.unpack(">I", frame[2:6])[0]
    end = 6 + payload_length
    if len(frame) < end + 4:
        raise ValueError("Truncated NARCIS frame")
    expected_crc = struct.unpack(">I", frame[end : end + 4])[0]
    if zlib.crc32(frame[:end]) & 0xFFFFFFFF != expected_crc:
        raise ValueError("CRC verification failed")
    return frame[6:end], len(errata)


def bits_to_symbols(bits: list[int], bits_per_symbol: int) -> tuple[list[int], int]:
    if bits_per_symbol <= 0:
        raise ValueError("bits_per_symbol must be positive")
    padding = (-len(bits)) % bits_per_symbol
    padded = bits + [0] * padding
    symbols = [
        sum(
            padded[index + offset] << (bits_per_symbol - 1 - offset)
            for offset in range(bits_per_symbol)
        )
        for index in range(0, len(padded), bits_per_symbol)
    ]
    return symbols, padding


def symbols_to_bits(
    symbols: list[int], bits_per_symbol: int, padding: int
) -> list[int]:
    bits = [
        (symbol >> shift) & 1
        for symbol in symbols
        for shift in range(bits_per_symbol - 1, -1, -1)
    ]
    return bits[:-padding] if padding else bits
