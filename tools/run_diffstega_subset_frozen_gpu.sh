#!/usr/bin/env bash
set -euo pipefail

SUBSET="${1:?Usage: run_diffstega_subset_frozen_gpu.sh <similar|content|style> <work-root>}"
WORK_ROOT="${2:?Usage: run_diffstega_subset_frozen_gpu.sh <similar|content|style> <work-root>}"
NARCIS_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIFFSTEGA_ROOT="$WORK_ROOT/DiffStega"
EVIDENCE_ROOT="$WORK_ROOT/evidence"

if [[ ! -f "$EVIDENCE_ROOT/preflight.json" ]]; then
  echo "Missing preflight.json: run prepare_diffstega_frozen_gpu.sh first." >&2
  exit 21
fi
if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "A CUDA-capable NVIDIA runtime is required." >&2
  exit 20
fi

cd "$DIFFSTEGA_ROOT"
case "$SUBSET" in
  similar)
    mkdir -p output/UniStega_similar
    /usr/bin/time -v python main.py \
      --yaml_path ./dataset/UniStega/similar_prompts/config.yaml \
      --save_path ./output/UniStega_similar \
      --null_prompt1 --optional_control auto \
      > >(tee "$EVIDENCE_ROOT/similar.stdout.log") \
      2> >(tee "$EVIDENCE_ROOT/similar.stderr.log" >&2)
    ;;
  content)
    mkdir -p output/UniStega_content
    /usr/bin/time -v python main.py \
      --yaml_path ./dataset/UniStega/content_prompts/config.yaml \
      --save_path ./output/UniStega_content \
      --null_prompt1 --optional_control auto \
      > >(tee "$EVIDENCE_ROOT/content.stdout.log") \
      2> >(tee "$EVIDENCE_ROOT/content.stderr.log" >&2)
    ;;
  style)
    mkdir -p output/UniStega_style
    /usr/bin/time -v python main.py \
      --yaml_path ./dataset/UniStega/style_prompts/config.yaml \
      --save_path ./output/UniStega_style \
      --null_prompt1 --edit_strength 0.7 --single_model --rand_pw --optional_control auto \
      > >(tee "$EVIDENCE_ROOT/style.stdout.log") \
      2> >(tee "$EVIDENCE_ROOT/style.stderr.log" >&2)
    ;;
  *)
    echo "Unknown subset '$SUBSET'; expected similar, content, or style." >&2
    exit 22
    ;;
esac

date -u +%Y-%m-%dT%H:%M:%SZ > "$EVIDENCE_ROOT/${SUBSET}.completed_utc.txt"

python - <<'PY' "$DIFFSTEGA_ROOT" "$EVIDENCE_ROOT" "$SUBSET"
from pathlib import Path
import hashlib, json, sys
root = Path(sys.argv[1]); evidence = Path(sys.argv[2]); subset = sys.argv[3]
folder = {"similar":"UniStega_similar","content":"UniStega_content","style":"UniStega_style"}[subset]
output = root / "output" / folder
rows=[]
for path in sorted(p for p in output.rglob("*") if p.is_file()):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""):
            h.update(block)
    rows.append({"subset":folder,"path":path.relative_to(root).as_posix(),"bytes":path.stat().st_size,"sha256":h.hexdigest()})
(evidence/f"{subset}_output_manifest.json").write_text(json.dumps(rows,indent=2),encoding="utf-8")
print(json.dumps({"subset":subset,"files":len(rows)},indent=2))
PY

echo "DiffStega subset '$SUBSET' completed."
