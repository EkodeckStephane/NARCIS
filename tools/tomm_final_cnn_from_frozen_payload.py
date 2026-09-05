from __future__ import annotations

from argparse import ArgumentParser
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import zlib

import numpy as np
import pandas as pd
import sklearn
import torch
import torch.nn.functional as F
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from tomm_final_detector_audit import cnn_probabilities, safe_auc

FROZEN_PAYLOAD_SHA256 = "ac7fefd1e216e11216ac3575beb7de37874523d9efbd00972c9c6186088b7431"


def decode_frozen_payload() -> Path:
    payload_dir = ROOT / "tools" / ".tomm_frozen_payload"
    parts = sorted(payload_dir.glob("part*.b64"))
    if [p.name for p in parts] != [f"part{i:02d}.b64" for i in range(5)]:
        raise RuntimeError(f"expected five frozen payload parts, found {[p.name for p in parts]}")
    encoded = "".join(p.read_text(encoding="utf-8").strip() for p in parts)
    import base64

    decoded = zlib.decompress(base64.b64decode(encoded))
    actual = hashlib.sha256(decoded).hexdigest()
    if actual != FROZEN_PAYLOAD_SHA256:
        raise RuntimeError(f"frozen payload SHA mismatch: {actual} != {FROZEN_PAYLOAD_SHA256}")
    runtime_path = ROOT / "tools" / ".tomm_frozen_payload_runtime.py"
    runtime_path.write_bytes(decoded)
    return runtime_path


def load_payload(path: Path):
    spec = importlib.util.spec_from_file_location("tomm_frozen_payload_runtime", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not create frozen payload module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_cnn_images(dataset) -> torch.Tensor:
    rows = []
    for position in range(len(dataset)):
        image, _ = dataset[position]
        rows.append(
            F.interpolate(
                image.unsqueeze(0),
                size=(64, 64),
                mode="bilinear",
                align_corners=False,
                antialias=True,
            ).squeeze(0)
        )
        if (position + 1) % 500 == 0:
            print(f"cnn images: {position + 1}/{len(dataset)}", flush=True)
    return torch.stack(rows)


def run_cnn_chunk(*, dataset, target: np.ndarray, seed: int, output: Path, repeat_start: int, repeat_count: int):
    if target.shape != (7000, 30):
        raise RuntimeError(f"unexpected target shape: {target.shape}")
    if repeat_start < 0 or repeat_count < 1 or repeat_start + repeat_count > 20:
        raise RuntimeError("repeat chunk must lie within frozen repeats 0..19")

    output.mkdir(parents=True, exist_ok=True)
    cnn_images = build_cnn_images(dataset)
    indices = np.arange(len(dataset))
    repetition_rows = []
    head_rows = []

    for repeat in range(repeat_start, repeat_start + repeat_count):
        split_seed = seed * 10000 + repeat
        train, test = train_test_split(
            indices,
            test_size=0.35,
            random_state=split_seed,
            shuffle=True,
        )
        print(
            f"CNN seed={seed} repeat={repeat} split_seed={split_seed} train={len(train)} test={len(test)}",
            flush=True,
        )
        score = cnn_probabilities(cnn_images, target, train, test, split_seed)
        auc = [safe_auc(target[test, head], score[:, head]) for head in range(target.shape[1])]

        for head, value in enumerate(auc):
            head_rows.append(
                {
                    "dataset": "Caltech-101",
                    "partition_seed": seed,
                    "repeat": repeat,
                    "split_seed": split_seed,
                    "detector": "cnn30head",
                    "session": head,
                    "auc": value,
                    "train_positives": int(target[train, head].sum()),
                    "test_positives": int(target[test, head].sum()),
                    "train_images": len(train),
                    "test_images": len(test),
                }
            )
        macro = float(np.nanmean(auc))
        repetition_rows.append(
            {
                "dataset": "Caltech-101",
                "partition_seed": seed,
                "repeat": repeat,
                "split_seed": split_seed,
                "cnn30head_macro_auc": macro,
                "valid_cnn_heads": int(np.isfinite(auc).sum()),
            }
        )
        print(f"CNN seed={seed} repeat={repeat} macro_auc={macro:.9f}", flush=True)
        pd.DataFrame(repetition_rows).to_csv(output / "detector_repetitions.partial.csv", index=False)
        pd.DataFrame(head_rows).to_csv(output / "detector_heads.partial.csv", index=False)

    repetitions = pd.DataFrame(repetition_rows)
    heads = pd.DataFrame(head_rows)
    repetitions.to_csv(output / "detector_repetitions.csv", index=False)
    heads.to_csv(output / "detector_heads.csv", index=False)
    return repetitions, heads


def summarize_cnn(repetitions: pd.DataFrame) -> dict:
    values = repetitions["cnn30head_macro_auc"].to_numpy(dtype=float)
    return {
        "cnn30head_macro_auc": {
            "mean": float(np.nanmean(values)),
            "std": float(np.nanstd(values, ddof=1)) if np.isfinite(values).sum() > 1 else 0.0,
            "min": float(np.nanmin(values)),
            "max": float(np.nanmax(values)),
            "repeats": int(np.isfinite(values).sum()),
        }
    }


def main() -> None:
    parser = ArgumentParser(description="CNN-only final TOMM detector audit from the certified compact frozen schedule")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True, choices=(11, 29, 47, 71, 101))
    parser.add_argument("--repeat-start", type=int, required=True, choices=(0, 5, 10, 15))
    parser.add_argument("--repeat-count", type=int, default=5)
    args = parser.parse_args()

    payload_path = decode_frozen_payload()
    payload = load_payload(payload_path)

    def patched_run_detectors(*, dataset, target, seed, output, repeats):
        if repeats != args.repeat_count:
            raise RuntimeError(f"payload repeat count mismatch: {repeats} != {args.repeat_count}")
        return run_cnn_chunk(
            dataset=dataset,
            target=target,
            seed=seed,
            output=output,
            repeat_start=args.repeat_start,
            repeat_count=args.repeat_count,
        )

    payload.run_detectors = patched_run_detectors
    payload.summarize = summarize_cnn

    original_argv = sys.argv[:]
    try:
        sys.argv = [
            str(payload_path),
            "--dataset-root",
            str(args.dataset_root),
            "--output",
            str(args.output),
            "--seed",
            str(args.seed),
            "--repeats",
            str(args.repeat_count),
        ]
        payload.main()
    finally:
        sys.argv = original_argv
        try:
            payload_path.unlink()
        except FileNotFoundError:
            pass

    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "frozen_payload_sha256": FROZEN_PAYLOAD_SHA256,
        "partition_seed": args.seed,
        "repeat_start": args.repeat_start,
        "repeat_count": args.repeat_count,
        "split_seeds": [args.seed * 10000 + r for r in range(args.repeat_start, args.repeat_start + args.repeat_count)],
    }
    (args.output / "cnn_chunk_environment.json").write_text(
        json.dumps(environment, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(json.dumps(environment, indent=2), flush=True)


if __name__ == "__main__":
    main()
