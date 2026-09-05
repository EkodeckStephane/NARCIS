#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_COMMIT="73cd7cb8d102f4fc0f5bb168a71cfb948077d89a"
WORK_ROOT="${1:-diffstega_external_work}"
NARCIS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIFFSTEGA_ROOT="$WORK_ROOT/DiffStega"
EVIDENCE_ROOT="$WORK_ROOT/evidence"

mkdir -p "$WORK_ROOT" "$EVIDENCE_ROOT"

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "A CUDA-capable GPU runtime is required for the faithful DiffStega reproduction." >&2
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

python - <<'PY' "$DIFFSTEGA_ROOT"
from pathlib import Path
import sys
from huggingface_hub import hf_hub_download
root = Path(sys.argv[1])
assets = [
    ("h94/IP-Adapter", "models/ip-adapter-plus_sd15.bin", root / "pretrained_models" / "ip-adapter-plus_sd15.bin"),
    ("h94/IP-Adapter", "models/ip-adapter-plus-face_sd15.bin", root / "pretrained_models" / "ip-adapter-plus-face_sd15.bin"),
    ("h94/IP-Adapter", "models/image_encoder/pytorch_model.bin", root / "pretrained_models" / "image_encoder_for_ip_adapter" / "pytorch_model.bin"),
    ("h94/IP-Adapter", "models/image_encoder/config.json", root / "pretrained_models" / "image_encoder_for_ip_adapter" / "config.json"),
]
for repo, filename, destination in assets:
    destination.parent.mkdir(parents=True, exist_ok=True)
    downloaded = Path(hf_hub_download(repo_id=repo, filename=filename))
    if destination.exists():
        destination.unlink()
    destination.write_bytes(downloaded.read_bytes())
    print(destination)
PY

if [[ ! -d "$DIFFSTEGA_ROOT/dataset/UniStega" && ! -d "$DIFFSTEGA_ROOT/dataset/Unistega" ]]; then
  python -m gdown 'https://drive.google.com/uc?id=1ITaNvYAP8hB32TxwEo4Rdf-515plUOdA' -O "$WORK_ROOT/unistega_download"
  FILE_TYPE="$(file -b "$WORK_ROOT/unistega_download" || true)"
  echo "$FILE_TYPE" | tee "$EVIDENCE_ROOT/unistega_file_type.txt"
  mkdir -p "$DIFFSTEGA_ROOT/dataset"
  if [[ "$FILE_TYPE" == *Zip* ]]; then
    unzip -q "$WORK_ROOT/unistega_download" -d "$DIFFSTEGA_ROOT/dataset"
  else
    tar -xf "$WORK_ROOT/unistega_download" -C "$DIFFSTEGA_ROOT/dataset"
  fi
fi

python "$NARCIS_ROOT/tools/diffstega_gpu_preflight.py" \
  --diffstega-root "$DIFFSTEGA_ROOT" \
  --output "$EVIDENCE_ROOT/preflight.json"

cd "$DIFFSTEGA_ROOT"
mkdir -p output/UniStega_similar output/UniStega_content output/UniStega_style

/usr/bin/time -v python main.py \
  --yaml_path ./dataset/UniStega/similar_prompts/config.yaml \
  --save_path ./output/UniStega_similar \
  --null_prompt1 --optional_control auto \
  > >(tee "$EVIDENCE_ROOT/similar.stdout.log") \
  2> >(tee "$EVIDENCE_ROOT/similar.stderr.log" >&2)

/usr/bin/time -v python main.py \
  --yaml_path ./dataset/UniStega/content_prompts/config.yaml \
  --save_path ./output/UniStega_content \
  --null_prompt1 --optional_control auto \
  > >(tee "$EVIDENCE_ROOT/content.stdout.log") \
  2> >(tee "$EVIDENCE_ROOT/content.stderr.log" >&2)

/usr/bin/time -v python main.py \
  --yaml_path ./dataset/UniStega/style_prompts/config.yaml \
  --save_path ./output/UniStega_style \
  --null_prompt1 --edit_strength 0.7 --single_model --rand_pw --optional_control auto \
  > >(tee "$EVIDENCE_ROOT/style.stdout.log") \
  2> >(tee "$EVIDENCE_ROOT/style.stderr.log" >&2)

cd "$NARCIS_ROOT"
python - <<'PY' "$DIFFSTEGA_ROOT" "$EVIDENCE_ROOT"
from pathlib import Path
import hashlib
import json
import sys
root = Path(sys.argv[1])
evidence = Path(sys.argv[2])
rows = []
for subset in ("UniStega_similar", "UniStega_content", "UniStega_style"):
    output = root / "output" / subset
    for path in sorted(p for p in output.rglob("*") if p.is_file()):
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append({"subset": subset, "path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": h})
(evidence / "output_manifest.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(json.dumps({"files": len(rows), "manifest": str(evidence / 'output_manifest.json')}, indent=2))
PY
