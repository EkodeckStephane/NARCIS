from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from narcis.data import discover_images
from run_bossbase_campaign import train_encoder

EXPECTED_CHECKPOINT_SHA256 = {
    11: "0adac1e014b799ada4a46698bcad922ce4ce116697186c1d45964e405a81e28c",
    29: "658e97d5fe4ad8da03ebad42461bce458d967beaf5753ac5d22a3c62eb480f2e",
    47: "426d058567fbb08eca9a34668c1a20caeb29ba8d5c7b6ba0d2e8c44c449c6a2a",
    71: "e0e958faf040a4d080d377a7694ea86cd602eab7c5350d4f04e619ca37fcade4",
    101: "810f843f82cd6726b16ae632d38ec6bb0f1dbfaaf0345ffd92a6a0a883cb722e",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = ArgumentParser(description="Regenerate and verify one canonical ARCIS Caltech checkpoint")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True, choices=tuple(EXPECTED_CHECKPOINT_SHA256))
    parser.add_argument("--epochs", type=int, default=5)
    args = parser.parse_args()

    args.checkpoint_root.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)

    paths = discover_images(args.dataset_root.resolve())
    if len(paths) < 8500:
        raise ValueError(f"Caltech-101 requires >=8500 images, found {len(paths)}")

    order = np.random.default_rng(args.seed).permutation(len(paths))
    train_paths = [paths[position] for position in order[:1500]]

    _, history = train_encoder(
        train_paths,
        args.seed,
        args.epochs,
        128,
        64,
        args.output,
        checkpoint_root=args.checkpoint_root,
        input_mode="RGB",
        channel_size=256,
    )
    if history:
        pd.DataFrame(history).to_csv(args.output / "training_history.csv", index=False)

    checkpoint = args.checkpoint_root / f"encoder_seed_{args.seed}.pt"
    actual = sha256_file(checkpoint)
    expected = EXPECTED_CHECKPOINT_SHA256[args.seed]
    manifest = {
        "seed": args.seed,
        "source_images": len(paths),
        "train_images": len(train_paths),
        "epochs": args.epochs,
        "expected_sha256": expected,
        "actual_sha256": actual,
        "matches_recorded_fresh_campaign": actual == expected,
    }
    (args.output / "checkpoint_sha_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))
    if actual != expected:
        raise SystemExit("Regenerated checkpoint SHA does not match recorded fresh campaign")


if __name__ == "__main__":
    main()
