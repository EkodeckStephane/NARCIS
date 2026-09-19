from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

BUNDLE_SHA256 = "8193bb8462d5b79fb18462e8e55091b8982752161ed388e95b7b7785483ed1f1"
HOLDOUT_SHA256 = "27f99fa00e9e8a7f1792195799615e8c8235718fa613fc20476a9f6014c70fcf"

CHECKPOINTS = {
    11: "0adac1e014b799ada4a46698bcad922ce4ce116697186c1d45964e405a81e28c",
    29: "658e97d5fe4ad8da03ebad42461bce458d967beaf5753ac5d22a3c62eb480f2e",
    47: "426d058567fbb08eca9a34668c1a20caeb29ba8d5c7b6ba0d2e8c44c449c6a2a",
    71: "e0e958faf040a4d080d377a7694ea86cd602eab7c5350d4f04e619ca37fcade4",
    101: "810f843f82cd6726b16ae632d38ec6bb0f1dbfaaf0345ffd92a6a0a883cb722e",
}

EXPECTED_RUNTIME = {
    "python_prefix": "3.13.5",
    "torch": "2.10.0+cpu",
    "numpy": "2.3.5",
    "pandas": "2.2.3",
    "scikit_learn": "1.8.0",
    "scipy": "1.17.0",
    "pillow": "12.3.0",
    "cryptography": "46.0.4",
}

EXPECTED_PER_SEED = {
    11: (240, 240, 55),
    29: (240, 214, 64),
    47: (240, 240, 37),
    71: (240, 231, 64),
    101: (240, 238, 63),
}

EXPECTED_BY_ATTACK = {
    "gaussian_9_holdout": (150, 150),
    "gaussian_15_holdout": (150, 150),
    "blur_1.2_holdout": (150, 150),
    "blur_1.8_holdout": (150, 150),
    "crop_08_holdout": (150, 150),
    "crop_12_holdout": (150, 113),
    "rotate_5_holdout": (150, 150),
    "rotate_9_holdout": (150, 150),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_bundle(path: Path) -> dict:
    observed_bundle = sha256_file(path)
    if observed_bundle != BUNDLE_SHA256:
        raise SystemExit(
            f"checkpoint bundle SHA mismatch: expected {BUNDLE_SHA256}, got {observed_bundle}"
        )

    observed = {}
    with zipfile.ZipFile(path) as archive:
        runtime = json.loads(archive.read("runtime_environment.json"))
        if not str(runtime["python"]).startswith(EXPECTED_RUNTIME["python_prefix"]):
            raise SystemExit(f"runtime Python mismatch: {runtime['python']}")
        for key, value in EXPECTED_RUNTIME.items():
            if key == "python_prefix":
                continue
            if str(runtime.get(key)) != value:
                raise SystemExit(
                    f"runtime {key} mismatch: expected {value}, got {runtime.get(key)}"
                )

        for seed, expected in CHECKPOINTS.items():
            member = f"checkpoints/caltech101/encoder_seed_{seed}.pt"
            actual = sha256_bytes(archive.read(member))
            observed[seed] = actual
            if actual != expected:
                raise SystemExit(
                    f"seed {seed} checkpoint mismatch: expected {expected}, got {actual}"
                )

    return {
        "bundle_sha256": observed_bundle,
        "checkpoint_sha256": {str(k): v for k, v in observed.items()},
        "runtime": runtime,
    }


def verify_holdout(path: Path) -> dict:
    observed = sha256_file(path)
    if observed != HOLDOUT_SHA256:
        raise SystemExit(
            f"holdout aggregate SHA mismatch: expected {HOLDOUT_SHA256}, got {observed}"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    aggregate = data["aggregate"]
    if (aggregate["trials"], aggregate["successes"], aggregate["maximum_rs_corrections"]) != (
        1200,
        1163,
        64,
    ):
        raise SystemExit(f"unexpected aggregate result: {aggregate}")

    per_seed = {}
    for row in data["per_seed"]:
        seed = int(row["seed"])
        observed_tuple = (
            int(row["trials"]),
            int(row["successes"]),
            int(row["maximum_rs_corrections"]),
        )
        if observed_tuple != EXPECTED_PER_SEED[seed]:
            raise SystemExit(
                f"seed {seed} result mismatch: expected {EXPECTED_PER_SEED[seed]}, got {observed_tuple}"
            )
        per_seed[seed] = observed_tuple

    by_attack = {}
    for name, expected in EXPECTED_BY_ATTACK.items():
        row = data["by_attack"][name]
        observed_tuple = (int(row["trials"]), int(row["successes"]))
        if observed_tuple != expected:
            raise SystemExit(
                f"attack {name} mismatch: expected {expected}, got {observed_tuple}"
            )
        by_attack[name] = observed_tuple

    return {
        "aggregate_sha256": observed,
        "aggregate": aggregate,
        "per_seed": {str(k): list(v) for k, v in per_seed.items()},
        "by_attack": {k: list(v) for k, v in by_attack.items()},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-bundle", type=Path, required=True)
    parser.add_argument("--holdout-aggregate", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = {
        "status": "PASS",
        "canonical_checkpoint_bundle": verify_bundle(args.checkpoint_bundle),
        "canonical_holdout": verify_holdout(args.holdout_aggregate),
        "interpretation": (
            "A4 canonical lineage is byte-identified by the archived checkpoint bundle "
            "and the archived holdout aggregate. Regenerated checkpoints from a different "
            "runtime are diagnostic only and are not substituted for the canonical bytes."
        ),
    }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
