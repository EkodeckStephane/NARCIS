from __future__ import annotations

from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path
import hashlib
import importlib.metadata
import json
import math
import platform
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image
import torch
import torch.nn.functional as F
from torchvision.transforms import functional as TF
import yaml
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


EXPECTED_COUNTS = {
    "content": 42,
    "style": 28,
    "similar": 30,
}
SUBSET_LAYOUT = {
    "content": ("content_prompts", "UniStega_content"),
    "style": ("style_prompts", "UniStega_style"),
    "similar": ("similar_prompts", "UniStega_similar"),
}
REQUIRED_FAMILIES = ("original", "encrypted", "correct", "no_password", "wrong_password")
METRIC_COLUMNS = (
    "encrypted_psnr", "encrypted_ssim", "encrypted_lpips", "encrypted_id_sim",
    "encrypted_clip_score", "encrypted_niqe",
    "correct_psnr", "correct_ssim", "correct_lpips", "correct_id_sim",
    "no_password_psnr", "no_password_ssim", "no_password_lpips", "no_password_id_sim",
    "wrong_password_psnr", "wrong_password_ssim", "wrong_password_lpips", "wrong_password_id_sim",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def discover_dataset_root(diffstega_root: Path) -> Path:
    dataset = diffstega_root / "dataset"
    candidates = (dataset / "UniStega", dataset / "Unistega", dataset)
    for candidate in candidates:
        if all((candidate / prompt_dir).is_dir() for prompt_dir, _ in SUBSET_LAYOUT.values()):
            return candidate
    raise RuntimeError("Unable to locate the three official UniStega prompt directories")


def load_rgb(path: Path) -> Image.Image:
    with Image.open(path) as im:
        return im.convert("RGB").copy()


def unique_match(paths: list[Path]) -> tuple[Path | None, str | None]:
    paths = sorted(paths)
    if len(paths) == 1:
        return paths[0], None
    if not paths:
        return None, "missing"
    return None, "ambiguous:" + ",".join(p.name for p in paths)


def discover_case_outputs(output_root: Path, stem: str) -> tuple[dict[str, Path | None], dict[str, str | None]]:
    original, e0 = unique_match([output_root / f"{stem}.png"] if (output_root / f"{stem}.png").exists() else [])
    encrypted, e1 = unique_match(list(output_root.glob(f"{stem}_hide_pw_*.png")))
    correct, e2 = unique_match(list(output_root.glob(f"{stem}_rec_w_*.png")))
    wrong_candidates = list(output_root.glob(f"{stem}_rec_wo_*_w_*.png"))
    wrong_password, e4 = unique_match(wrong_candidates)
    no_candidates = [
        p for p in output_root.glob(f"{stem}_rec_wo_*.png")
        if p not in wrong_candidates and "_w_" not in p.name[len(stem) + len("_rec_wo_"):]
    ]
    no_password, e3 = unique_match(no_candidates)
    return (
        {
            "original": original,
            "encrypted": encrypted,
            "correct": correct,
            "no_password": no_password,
            "wrong_password": wrong_password,
        },
        {
            "original": e0,
            "encrypted": e1,
            "correct": e2,
            "no_password": e3,
            "wrong_password": e4,
        },
    )


def arrays_same_size(a: Image.Image, b: Image.Image) -> tuple[np.ndarray, np.ndarray]:
    if a.size != b.size:
        raise ValueError(f"image size mismatch: {a.size} != {b.size}")
    return np.asarray(a, dtype=np.uint8), np.asarray(b, dtype=np.uint8)


def psnr_ssim(a: Image.Image, b: Image.Image) -> tuple[float, float]:
    aa, bb = arrays_same_size(a, b)
    psnr = float(peak_signal_noise_ratio(aa, bb, data_range=255))
    ssim = float(structural_similarity(aa, bb, channel_axis=2, data_range=255))
    return psnr, ssim


def to_lpips_tensor(image: Image.Image, device: torch.device) -> torch.Tensor:
    return (TF.to_tensor(image).unsqueeze(0).to(device) * 2.0 - 1.0)


def safe_float(value: Any) -> float:
    x = float(value)
    return x if math.isfinite(x) else float("nan")


def main() -> None:
    parser = ArgumentParser(description="Frozen independent evaluator for reproduced DiffStega UniStega outputs")
    parser.add_argument("--diffstega-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    args = parser.parse_args()

    root = args.diffstega_root.resolve()
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_root = discover_dataset_root(root)

    if args.device == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("--device cuda requested but CUDA is unavailable")
        device = torch.device("cuda")
    elif args.device == "cpu":
        device = torch.device("cpu")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Load frozen independent metric implementations only after output discovery is fixed.
    import lpips
    from facenet_pytorch import MTCNN, InceptionResnetV1
    from transformers import CLIPModel, CLIPProcessor
    import pyiqa
    from huggingface_hub import model_info

    lpips_model = lpips.LPIPS(net="alex").to(device).eval()
    mtcnn = MTCNN(image_size=160, margin=0, post_process=True, device=device)
    facenet = InceptionResnetV1(pretrained="vggface2").to(device).eval()
    clip_id = "openai/clip-vit-base-patch32"
    clip_model = CLIPModel.from_pretrained(clip_id).to(device).eval()
    clip_processor = CLIPProcessor.from_pretrained(clip_id)
    niqe_model = pyiqa.create_metric("niqe", device=device)

    try:
        clip_revision = model_info(clip_id).sha
    except Exception as error:
        clip_revision = f"unresolved:{type(error).__name__}:{error}"

    consumed_files: dict[str, dict[str, Any]] = {}

    def consume(path: Path) -> None:
        key = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
        if key not in consumed_files:
            consumed_files[key] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}

    @torch.no_grad()
    def lpips_value(a: Image.Image, b: Image.Image) -> float:
        arrays_same_size(a, b)
        return safe_float(lpips_model(to_lpips_tensor(a, device), to_lpips_tensor(b, device)).item())

    @torch.no_grad()
    def face_id_similarity(a: Image.Image, b: Image.Image) -> tuple[float, bool]:
        fa = mtcnn(a)
        fb = mtcnn(b)
        if fa is None or fb is None:
            return float("nan"), True
        ea = F.normalize(facenet(fa.unsqueeze(0).to(device)), dim=1)
        eb = F.normalize(facenet(fb.unsqueeze(0).to(device)), dim=1)
        return safe_float((ea * eb).sum(dim=1).item()), False

    @torch.no_grad()
    def clip_score(image: Image.Image, caption: str) -> float:
        image_inputs = clip_processor(images=[image], return_tensors="pt")
        text_inputs = clip_processor(text=[caption], return_tensors="pt", padding=True, truncation=True)
        image_features = clip_model.get_image_features(pixel_values=image_inputs["pixel_values"].to(device))
        text_features = clip_model.get_text_features(
            input_ids=text_inputs["input_ids"].to(device),
            attention_mask=text_inputs["attention_mask"].to(device),
        )
        image_features = F.normalize(image_features, dim=1)
        text_features = F.normalize(text_features, dim=1)
        return safe_float(100.0 * torch.clamp((image_features * text_features).sum(), min=0).item())

    @torch.no_grad()
    def niqe_value(image: Image.Image) -> float:
        tensor = TF.to_tensor(image).unsqueeze(0).to(device)
        return safe_float(niqe_model(tensor).item())

    rows: list[dict[str, Any]] = []
    expected_total = 0

    for subset, expected_count in EXPECTED_COUNTS.items():
        prompt_dir, output_name = SUBSET_LAYOUT[subset]
        config_path = dataset_root / prompt_dir / "config.yaml"
        consume(config_path)
        with config_path.open("r", encoding="utf-8") as f:
            cases = yaml.safe_load(f)
        if not isinstance(cases, list) or len(cases) != expected_count:
            raise RuntimeError(f"{subset}: expected {expected_count} YAML cases, got {len(cases) if isinstance(cases, list) else type(cases)}")
        expected_total += len(cases)
        result_root = root / "output" / output_name

        for ordinal, case in enumerate(cases):
            source_rel = str(case["image_path"])
            stem = Path(source_rel).stem
            target_caption = str(case["target_caption"])
            control = str(case.get("optional_control", ""))
            face_case = control == "landmark"
            paths, discovery_errors = discover_case_outputs(result_root, stem)

            row: dict[str, Any] = {
                "subset": subset,
                "ordinal": ordinal,
                "image_path": source_rel,
                "image_stem": stem,
                "target_caption": target_caption,
                "optional_control": control,
                "face_case": face_case,
            }
            for family in REQUIRED_FAMILIES:
                path = paths[family]
                row[f"{family}_path"] = path.relative_to(root).as_posix() if path is not None else None
                row[f"{family}_discovery_error"] = discovery_errors[family]
                if path is not None:
                    consume(path)
                    row[f"{family}_sha256"] = consumed_files[path.relative_to(root).as_posix()]["sha256"]
                else:
                    row[f"{family}_sha256"] = None

            row["case_complete"] = all(paths[x] is not None for x in REQUIRED_FAMILIES)
            row["evaluation_error"] = None
            row["face_detection_failure"] = False
            for metric in METRIC_COLUMNS:
                row[metric] = float("nan")

            if not row["case_complete"]:
                rows.append(row)
                continue

            try:
                images = {family: load_rgb(path) for family, path in paths.items() if path is not None}
                original = images["original"]
                for family, prefix in (
                    ("encrypted", "encrypted"),
                    ("correct", "correct"),
                    ("no_password", "no_password"),
                    ("wrong_password", "wrong_password"),
                ):
                    psnr, ssim = psnr_ssim(original, images[family])
                    row[f"{prefix}_psnr"] = psnr
                    row[f"{prefix}_ssim"] = ssim
                    row[f"{prefix}_lpips"] = lpips_value(original, images[family])
                    if face_case:
                        identity, failed = face_id_similarity(original, images[family])
                        row[f"{prefix}_id_sim"] = identity
                        row["face_detection_failure"] = bool(row["face_detection_failure"] or failed)
                row["encrypted_clip_score"] = clip_score(images["encrypted"], target_caption)
                row["encrypted_niqe"] = niqe_value(images["encrypted"])
            except Exception as error:
                row["evaluation_error"] = f"{type(error).__name__}: {error}"

            rows.append(row)

    if expected_total != 100 or len(rows) != 100:
        raise RuntimeError(f"Expected exactly 100 UniStega cases, got expected_total={expected_total}, rows={len(rows)}")

    raw = pd.DataFrame(rows)
    raw_path = output_dir / "diffstega_metrics_per_case.csv"
    raw.to_csv(raw_path, index=False)

    summaries: list[dict[str, Any]] = []
    for scope_name, frame in [("global", raw), *[(s, raw[raw["subset"] == s]) for s in EXPECTED_COUNTS]]:
        base = {
            "scope": scope_name,
            "cases": int(len(frame)),
            "complete_cases": int(frame["case_complete"].sum()),
            "evaluation_errors": int(frame["evaluation_error"].notna().sum()),
            "face_cases": int(frame["face_case"].sum()),
            "face_detection_failures": int(frame["face_detection_failure"].sum()),
        }
        for metric in METRIC_COLUMNS:
            values = pd.to_numeric(frame[metric], errors="coerce").to_numpy(dtype=float)
            finite = values[np.isfinite(values)]
            stats = {
                "metric": metric,
                "valid_n": int(len(finite)),
                "mean": float(np.mean(finite)) if len(finite) else float("nan"),
                "std": float(np.std(finite, ddof=1)) if len(finite) > 1 else float("nan"),
                "median": float(np.median(finite)) if len(finite) else float("nan"),
                "min": float(np.min(finite)) if len(finite) else float("nan"),
                "max": float(np.max(finite)) if len(finite) else float("nan"),
            }
            summaries.append({**base, **stats})

    summary = pd.DataFrame(summaries)
    summary_path = output_dir / "diffstega_metrics_summary.csv"
    summary.to_csv(summary_path, index=False)

    consumed_path = output_dir / "diffstega_consumed_files.json"
    consumed_path.write_text(json.dumps(consumed_files, indent=2, sort_keys=True), encoding="utf-8")

    try:
        pip_freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    except Exception as error:
        pip_freeze = f"ERROR: {type(error).__name__}: {error}\n"
    freeze_path = output_dir / "pip_freeze.txt"
    freeze_path.write_text(pip_freeze, encoding="utf-8")

    manifest = {
        "protocol": "TOMM_DIFFSTEGA_METRICS_FREEZE.md",
        "diffstega_root": str(root),
        "dataset_root": str(dataset_root),
        "device": str(device),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_runtime": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "packages": {
                name: package_version(name)
                for name in (
                    "numpy", "pandas", "Pillow", "scikit-image", "lpips", "facenet-pytorch",
                    "transformers", "huggingface-hub", "pyiqa", "PyYAML"
                )
            },
        },
        "models": {
            "lpips": {"package": "lpips", "backbone": "alex"},
            "facenet": {"implementation": "facenet-pytorch", "backbone": "InceptionResnetV1", "pretrained": "vggface2", "detector": "MTCNN"},
            "clip": {"identifier": clip_id, "resolved_revision": clip_revision},
            "niqe": {"implementation": "pyiqa", "metric": "niqe"},
        },
        "case_counts": {
            "total": int(len(raw)),
            "by_subset": {s: int((raw["subset"] == s).sum()) for s in EXPECTED_COUNTS},
            "complete": int(raw["case_complete"].sum()),
            "evaluation_errors": int(raw["evaluation_error"].notna().sum()),
            "face_detection_failures": int(raw["face_detection_failure"].sum()),
        },
        "artifacts": {},
    }

    for path in (raw_path, summary_path, consumed_path, freeze_path):
        manifest["artifacts"][path.name] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
    manifest_path = output_dir / "diffstega_metrics_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=True), encoding="utf-8")

    print(json.dumps(manifest, indent=2, allow_nan=True))
    if manifest["case_counts"]["complete"] != 100 or manifest["case_counts"]["evaluation_errors"] != 0:
        raise SystemExit("DiffStega metric evaluation completed with missing or failed cases; retain artifacts and inspect per-case CSV")


if __name__ == "__main__":
    main()
