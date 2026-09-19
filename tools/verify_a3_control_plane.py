from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cryptography.exceptions import InvalidTag

from narcis.security import ReplayGuard, SessionMetadata, open_metadata, seal_metadata

SEEDS = (11, 29, 47, 71, 101)
SENDER = "arcis-sender"
RECEIVER = "arcis-receiver"
PAYLOAD_COVERS = {8: 2320, 32: 2640, 64: 3070}


def key_for_seed(seed: int) -> bytes:
    return hashlib.sha256(f"ARCIS-A3-control-plane-{seed}".encode()).digest()


def run_seed(seed: int) -> dict:
    key = key_for_seed(seed)
    guard = ReplayGuard()
    roundtrips = 0
    tamper_rejected = False
    replay_rejected = False
    wrong_receiver_rejected = False
    envelope_lengths: list[int] = []

    for sequence in range(30):
        payload_bytes = (8, 32, 64)[sequence // 10]
        metadata = SessionMetadata(
            sequence=sequence,
            padding_bits=0,
            codebook_size=8,
            cover_count=PAYLOAD_COVERS[payload_bytes],
        )
        envelope = seal_metadata(metadata, key, SENDER, RECEIVER)
        envelope_lengths.append(len(envelope))
        opened = open_metadata(envelope, key, SENDER, RECEIVER, guard)
        if opened != metadata:
            raise RuntimeError(f"seed {seed} sequence {sequence}: metadata roundtrip mismatch")
        roundtrips += 1

        if sequence == 0:
            tampered = bytearray(envelope)
            tampered[-1] ^= 1
            try:
                open_metadata(bytes(tampered), key, SENDER, RECEIVER, ReplayGuard())
            except InvalidTag:
                tamper_rejected = True

            try:
                open_metadata(envelope, key, SENDER, RECEIVER, guard)
            except ValueError as error:
                if "Replay" in str(error):
                    replay_rejected = True
                else:
                    raise

            try:
                open_metadata(envelope, key, SENDER, "wrong-receiver", ReplayGuard())
            except InvalidTag:
                wrong_receiver_rejected = True

    if roundtrips != 30:
        raise RuntimeError(f"seed {seed}: expected 30 roundtrips, got {roundtrips}")
    if not (tamper_rejected and replay_rejected and wrong_receiver_rejected):
        raise RuntimeError(
            f"seed {seed}: negative control failed: "
            f"tamper={tamper_rejected}, replay={replay_rejected}, "
            f"wrong_receiver={wrong_receiver_rejected}"
        )

    return {
        "seed": seed,
        "roundtrips": roundtrips,
        "tamper_rejected": tamper_rejected,
        "replay_rejected": replay_rejected,
        "wrong_receiver_rejected": wrong_receiver_rejected,
        "metadata_envelope_bytes_min": min(envelope_lengths),
        "metadata_envelope_bytes_max": max(envelope_lengths),
        "metadata_envelope_bytes_mean": sum(envelope_lengths) / len(envelope_lengths),
    }


def main() -> None:
    rows = [run_seed(seed) for seed in SEEDS]
    report = {
        "status": "PASS",
        "protocol": {
            "metadata_fields": ["sequence", "padding_bits", "codebook_size", "cover_count"],
            "authenticated_encryption": "AES-GCM",
            "associated_data_binds": ["sender", "receiver"],
            "freshness": "strictly increasing per-sender sequence number",
        },
        "aggregate": {
            "seeds": len(rows),
            "roundtrips": sum(row["roundtrips"] for row in rows),
            "tamper_rejections": sum(bool(row["tamper_rejected"]) for row in rows),
            "replay_rejections": sum(bool(row["replay_rejected"]) for row in rows),
            "wrong_receiver_rejections": sum(bool(row["wrong_receiver_rejected"]) for row in rows),
        },
        "per_seed": rows,
    }
    output = Path("tomm_results/A3_AUTHENTICATED_CONTROL_PLANE_AUDIT.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
