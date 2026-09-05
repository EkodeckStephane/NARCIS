from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys

EXPECTED_COMMIT = "73cd7cb8d102f4fc0f5bb168a71cfb948077d89a"
EXPECTED_PYTHON = (3, 11, 5)
EXPECTED_COUNTS = {
    "content_prompts": 42,
    "style_prompts": 28,
    "similar_prompts": 30,
}
REQUIRED_FILES = (
    "pretrained_models/ip-adapter-plus_sd15.bin",
    "pretrained_models/ip-adapter-plus-face_sd15.bin",
    "pretrained_models/image_encoder_for_ip_adapter/pytorch_model.bin",
    "pretrained_models/image_encoder_for_ip_adapter/config.json",
)
EXPECTED_PACKAGES = {
    "torch": "2.1.0",
    "torchvision": "0.16.0",
    "torchaudio": "2.1.0",
    "diffusers": "0.26.3",
    "accelerate": "0.23.0",
    "transformers": "4.38.2",
    "controlnet-aux": "0.0.7",
}
LOCAL_BUILD_PACKAGES = {"torch", "torchvision", "torchaudio"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(root: Path, *args: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args], text=True, stderr=subprocess.STDOUT
        ).strip()
    except Exception:
        return None


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def package_matches(name: str, actual: str | None, expected: str) -> bool:
    if actual is None:
        return False
    # Official PyTorch wheels append a PEP 440 local build tag such as
    # +cpu or +cu121. The frozen package release remains 2.1.0/0.16.0.
    if name in LOCAL_BUILD_PACKAGES:
        return actual.split("+", 1)[0] == expected
    return actual == expected


def discover_unistega_root(root: Path) -> tuple[Path, str]:
    dataset = root / "dataset"
    candidates = (
        (dataset / "UniStega", "dataset/UniStega"),
        (dataset / "Unistega", "dataset/Unistega"),
        (dataset, "dataset archive root"),
    )
    for candidate, layout in candidates:
        if all((candidate / subset).is_dir() for subset in EXPECTED_COUNTS):
            return candidate, layout
    return dataset / "UniStega", "unresolved"


def main() -> None:
    parser = ArgumentParser(description="Preflight for the frozen DiffStega GPU reproduction")
    parser.add_argument("--diffstega-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.diffstega_root.resolve()
    tracked_changes = git_output(root, "diff", "--name-only", "HEAD")
    report = {
        "upstream_root": str(root),
        "expected_commit": EXPECTED_COMMIT,
        "actual_commit": git_output(root, "rev-parse", "HEAD"),
        "tracked_changes": tracked_changes,
        "environment": {
            "python": sys.version,
            "python_expected": ".".join(map(str, EXPECTED_PYTHON)),
            "platform": platform.platform(),
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "packages": {},
        },
        "assets": {},
        "unistega": {},
        "checks": {},
    }

    for package, expected in EXPECTED_PACKAGES.items():
        actual = package_version(package)
        report["environment"]["packages"][package] = {
            "expected": expected,
            "actual": actual,
            "matches": package_matches(package, actual, expected),
        }

    try:
        import torch
        report["environment"]["torch_runtime"] = {
            "version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_runtime": torch.version.cuda,
            "device_count": int(torch.cuda.device_count()),
            "devices": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
        }
    except Exception as error:
        report["environment"]["torch_runtime"] = {"error": f"{type(error).__name__}: {error}"}

    for relative in REQUIRED_FILES:
        path = root / relative
        report["assets"][relative] = {
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path) if path.exists() else None,
        }

    dataset_root, dataset_layout = discover_unistega_root(root)
    report["unistega"]["root"] = str(dataset_root)
    report["unistega"]["layout"] = dataset_layout
    total = 0
    for subset, expected in EXPECTED_COUNTS.items():
        subset_root = dataset_root / subset
        config = subset_root / "config.yaml"
        data_root = subset_root / "data"
        images = sorted(
            p for p in data_root.rglob("*")
            if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
        ) if data_root.exists() else []
        total += len(images)
        report["unistega"][subset] = {
            "expected_images": expected,
            "images_found": len(images),
            "config_exists": config.exists(),
            "config_sha256": sha256_file(config) if config.exists() else None,
            "sample_manifest_sha256": hashlib.sha256(
                "\n".join(p.relative_to(dataset_root).as_posix() for p in images).encode("utf-8")
            ).hexdigest(),
        }
    report["unistega"]["total_images_found"] = total

    package_ok = all(
        item["matches"] for item in report["environment"]["packages"].values()
    )
    torch_runtime = report["environment"].get("torch_runtime", {})
    report["checks"] = {
        "commit_matches": report["actual_commit"] == EXPECTED_COMMIT,
        "tracked_source_unchanged": tracked_changes == "",
        "python_matches": sys.version_info[:3] == EXPECTED_PYTHON,
        "packages_match": package_ok,
        "cuda_available": bool(torch_runtime.get("cuda_available", False)),
        "assets_present": all(item["exists"] for item in report["assets"].values()),
        "unistega_counts_match": all(
            report["unistega"][subset]["images_found"] == expected
            and report["unistega"][subset]["config_exists"]
            for subset, expected in EXPECTED_COUNTS.items()
        ),
    }
    report["ready"] = bool(all(report["checks"].values()))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["ready"]:
        raise SystemExit("DiffStega frozen GPU preflight failed; inspect the JSON manifest")


if __name__ == "__main__":
    main()
