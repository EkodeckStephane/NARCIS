from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json
import os
import platform
import sys

import numpy as np
import pandas as pd
import sklearn
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from narcis.data import discover_images
from run_bossbase_campaign import NativeImageDataset
from tomm_final_detector_audit import run_detectors, sha256_file, summarize


def canonical_identifiers(paths: list[Path], dataset_root: Path) -> list[str]:
    root = dataset_root.resolve()
    return [path.resolve().relative_to(root).as_posix() for path in paths]


def main() -> None:
    parser = ArgumentParser(description="Final detector audit consuming the certified NARCIS session schedule")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True, choices=(11, 29, 47, 71, 101))
    parser.add_argument("--repeats", type=int, default=20)
    args = parser.parse_args()

    dataset_root = args.dataset_root.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    target_path = args.output / "session_target.npy"
    schedule_path = args.output / "schedule.csv"
    channel_manifest_path = args.output / "channel_recheck_manifest.json"
    for required in (target_path, schedule_path, channel_manifest_path):
        if not required.exists():
            raise FileNotFoundError(required)

    paths = discover_images(dataset_root)
    if len(paths) < 8500:
        raise ValueError(f"Caltech-101 requires >=8500 images, found {len(paths)}")
    order = np.random.default_rng(args.seed).permutation(len(paths))
    index_paths = [paths[position] for position in order[1500:8500]]
    identifiers = canonical_identifiers(index_paths, dataset_root)
    dataset = NativeImageDataset(index_paths, "RGB", 256)

    target = np.load(target_path)
    if target.shape != (7000, 30):
        raise ValueError(f"expected session target shape (7000, 30), found {target.shape}")
    if not np.array_equal(target, target.astype(bool)):
        raise ValueError("session target must be binary")

    schedule = pd.read_csv(schedule_path)
    required_columns = {"image_index", "image_id", "sequence", "payload_bytes"}
    if not required_columns.issubset(schedule.columns):
        raise ValueError(f"schedule columns missing: {required_columns - set(schedule.columns)}")
    if len(schedule) != int(target.sum()):
        raise ValueError("schedule row count differs from session target emission count")
    reconstructed = np.zeros_like(target, dtype=np.uint8)
    for row in schedule.itertuples(index=False):
        image_index = int(row.image_index)
        sequence = int(row.sequence)
        if not (0 <= image_index < len(identifiers) and 0 <= sequence < target.shape[1]):
            raise ValueError("schedule index out of range")
        if str(row.image_id) != identifiers[image_index]:
            raise ValueError("schedule identifier does not match deterministic Caltech partition")
        reconstructed[image_index, sequence] = 1
    if not np.array_equal(reconstructed, target):
        raise RuntimeError("schedule.csv and session_target.npy encode different traffic")

    channel_manifest = json.loads(channel_manifest_path.read_text(encoding="utf-8"))
    schedule_sha = sha256_file(schedule_path)
    target_sha = sha256_file(target_path)
    if channel_manifest["artifacts"]["schedule_csv_sha256"] != schedule_sha:
        raise RuntimeError("schedule hash differs from channel manifest")
    if channel_manifest["artifacts"]["session_target_npy_sha256"] != target_sha:
        raise RuntimeError("session target hash differs from channel manifest")

    repetitions, heads = run_detectors(
        dataset=dataset,
        target=target,
        seed=args.seed,
        output=args.output,
        repeats=args.repeats,
    )
    manifest = {
        "dataset": "Caltech-101",
        "partition_seed": args.seed,
        "traffic_source": "aligned frozen channel recheck",
        "channel_manifest_sha256": sha256_file(channel_manifest_path),
        "checkpoint_actual_sha256": channel_manifest["checkpoint_actual_sha256"],
        "checkpoint_expected_sha256": channel_manifest["checkpoint_expected_sha256"],
        "checkpoint_matches_recorded_fresh_campaign": channel_manifest[
            "checkpoint_matches_recorded_fresh_campaign"
        ],
        "schedule": channel_manifest["schedule"],
        "detectors": summarize(repetitions),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "github_sha": os.environ.get("GITHUB_SHA"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        },
        "artifacts": {
            "schedule_csv_sha256": schedule_sha,
            "session_target_npy_sha256": target_sha,
            "detector_repetitions_csv_sha256": sha256_file(args.output / "detector_repetitions.csv"),
            "detector_heads_csv_sha256": sha256_file(args.output / "detector_heads.csv"),
        },
    }
    (args.output / "audit_manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=True), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, allow_nan=True), flush=True)


if __name__ == "__main__":
    main()
