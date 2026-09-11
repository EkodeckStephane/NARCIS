#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_COMMIT="73cd7cb8d102f4fc0f5bb168a71cfb948077d89a"
WORK_ROOT="${1:?Usage: prepare_diffstega_frozen_gpu.sh <work-root>}"
NARCIS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIFFSTEGA_ROOT="$WORK_ROOT/DiffStega"
EVIDENCE_ROOT="$WORK_ROOT/evidence"

mkdir -p "$WORK_ROOT" "$EVIDENCE_ROOT"

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "A CUDA-capable NVIDIA runtime is required." >&2
  exit 20
fi
nvidia-smi | tee "$EVIDENCE_ROOT/nvidia-smi.txt"

if [[ ! -d "$DIFFSTEGA_ROOT/.git" ]]; then
  git clone https://github.com/evtricks/DiffStega.git "$DIFFSTEGA_ROOT"
fi
git -C "$DIFFSTEGA_ROOT" fetch --all --tags
git -C "$DIFFSTEGA_ROOT" checkout --detach "$UPSTREAM_COMMIT"
git -C "$DIFFSTEGA_ROOT" reset --hard "$UPSTREAM_COMMIT"
git -C "$DIFFSTEGA_ROOT" clean -fdx -e pretrained_models -e dataset -e output

git -C "$DIFFSTEGA_ROOT" rev-parse HEAD | tee "$EVIDENCE_ROOT/upstream_commit.txt"
git -C "$DIFFSTEGA_ROOT" diff --name-only HEAD | tee "$EVIDENCE_ROOT/upstream_tracked_changes.txt"

python - <<'PY' "$DIFFSTEGA_ROOT" "$EVIDENCE_ROOT"
from pathlib import Path
import hashlib, json, sys
from huggingface_hub import hf_hub_download, model_info
root = Path(sys.argv[1]); evidence = Path(sys.argv[2])
repos = ["h94/IP-Adapter", "runwayml/stable-diffusion-v1-5", "GraydientPlatformAPI/picx-real"]
rev = {}
for repo in repos:
    try:
        info = model_info(repo)
        rev[repo] = {"sha": info.sha, "private": info.private, "gated": getattr(info, "gated", None)}
    except Exception as e:
        rev[repo] = {"error": f"{type(e).__name__}: {e}"}
(evidence / "model_revisions.json").write_text(json.dumps(rev, indent=2), encoding="utf-8")
assets = [
    ("h94/IP-Adapter", "models/ip-adapter-plus_sd15.bin", root / "pretrained_models" / "ip-adapter-plus_sd15.bin"),
    ("h94/IP-Adapter", "models/ip-adapter-plus-face_sd15.bin", root / "pretrained_models" / "ip-adapter-plus-face_sd15.bin"),
    ("h94/IP-Adapter", "models/image_encoder/pytorch_model.bin", root / "pretrained_models" / "image_encoder_for_ip_adapter" / "pytorch_model.bin"),
    ("h94/IP-Adapter", "models/image_encoder/config.json", root / "pretrained_models" / "image_encoder_for_ip_adapter" / "config.json"),
]
rows = []
for repo, filename, destination in assets:
    destination.parent.mkdir(parents=True, exist_ok=True)
    downloaded = Path(hf_hub_download(repo_id=repo, filename=filename))
    if not destination.exists() or destination.stat().st_size != downloaded.stat().st_size:
        destination.write_bytes(downloaded.read_bytes())
    h = hashlib.sha256(destination.read_bytes()).hexdigest()
    rows.append({"repo": repo, "filename": filename, "path": str(destination), "bytes": destination.stat().st_size, "sha256": h})
(evidence / "ip_adapter_assets.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
PY

DATASET_DIR="$DIFFSTEGA_ROOT/dataset"
if [[ ! -d "$DATASET_DIR/content_prompts" && ! -d "$DATASET_DIR/UniStega/content_prompts" && ! -d "$DATASET_DIR/Unistega/content_prompts" ]]; then
  python -m gdown 'https://drive.google.com/uc?id=1ITaNvYAP8hB32TxwEo4Rdf-515plUOdA' -O "$WORK_ROOT/unistega_download"
  FILE_TYPE="$(file -b "$WORK_ROOT/unistega_download" || true)"
  echo "$FILE_TYPE" | tee "$EVIDENCE_ROOT/unistega_file_type.txt"
  sha256sum "$WORK_ROOT/unistega_download" | tee "$EVIDENCE_ROOT/unistega_archive_sha256.txt"
  mkdir -p "$DATASET_DIR"
  if [[ "$FILE_TYPE" == *Zip* ]]; then
    unzip -q "$WORK_ROOT/unistega_download" -d "$DATASET_DIR"
  else
    tar -xf "$WORK_ROOT/unistega_download" -C "$DATASET_DIR"
  fi
fi

if [[ -d "$DATASET_DIR/content_prompts" && ! -e "$DATASET_DIR/UniStega" ]]; then
  (cd "$DATASET_DIR" && ln -s . UniStega)
elif [[ -d "$DATASET_DIR/Unistega/content_prompts" && ! -e "$DATASET_DIR/UniStega" ]]; then
  (cd "$DATASET_DIR" && ln -s Unistega UniStega)
fi

python "$NARCIS_ROOT/tools/diffstega_gpu_preflight.py" \
  --diffstega-root "$DIFFSTEGA_ROOT" \
  --output "$EVIDENCE_ROOT/preflight.json"

date -u +%Y-%m-%dT%H:%M:%SZ | tee "$EVIDENCE_ROOT/prepared_utc.txt"
echo "DiffStega frozen GPU preparation PASS"
