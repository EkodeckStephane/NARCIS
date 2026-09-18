#!/usr/bin/env bash
set -euo pipefail

# Portable launcher for an interactive free NVIDIA GPU notebook/runtime.
# It preserves the TOMM DiffStega freeze by creating an isolated Python 3.11.5
# environment and then delegating to run_diffstega_frozen_gpu.sh unchanged.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_ROOT="${1:-$ROOT/diffstega_external_work}"
ENV_ROOT="${DIFFSTEGA_ENV_ROOT:-$ROOT/.micromamba}"
MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-$ROOT/.mamba-root}"
export MAMBA_ROOT_PREFIX

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo 'No NVIDIA runtime detected. Enable a GPU accelerator before executing the frozen DiffStega benchmark.' >&2
  exit 20
fi
nvidia-smi

if [[ ! -x "$ENV_ROOT/bin/micromamba" ]]; then
  mkdir -p "$ENV_ROOT/bin"
  curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
    | tar -xj -C "$ENV_ROOT/bin" --strip-components=1 bin/micromamba
fi

if [[ ! -d "$MAMBA_ROOT_PREFIX/envs/diffstega-frozen" ]]; then
  "$ENV_ROOT/bin/micromamba" create -y -n diffstega-frozen -c conda-forge python=3.11.5 pip
fi

MM=("$ENV_ROOT/bin/micromamba" run -n diffstega-frozen)

"${MM[@]}" python -m pip install --upgrade 'pip<25'
"${MM[@]}" python -m pip install --index-url https://download.pytorch.org/whl/cu121 \
  torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0
"${MM[@]}" python -m pip install \
  'numpy<2' \
  diffusers==0.26.3 \
  accelerate==0.23.0 \
  transformers==4.38.2 \
  controlnet_aux==0.0.7 \
  huggingface_hub==0.20.3 \
  gdown==5.2.0

"${MM[@]}" python - <<'PY'
import json, sys, torch
state = {
    'python': sys.version,
    'torch': torch.__version__,
    'cuda_available': torch.cuda.is_available(),
    'cuda_runtime': torch.version.cuda,
    'device_count': torch.cuda.device_count(),
    'devices': [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
}
print(json.dumps(state, indent=2))
if sys.version_info[:3] != (3, 11, 5):
    raise SystemExit(f'Python freeze mismatch: {sys.version_info[:3]}')
if torch.__version__.split('+')[0] != '2.1.0':
    raise SystemExit(f'PyTorch freeze mismatch: {torch.__version__}')
if not torch.cuda.is_available():
    raise SystemExit('CUDA is unavailable in the isolated frozen environment')
PY

# Execute the already-frozen upstream protocol. `bash -lc` keeps the NARCIS
# wrapper unchanged while ensuring that `python` resolves inside micromamba.
"${MM[@]}" bash "$ROOT/tools/run_diffstega_frozen_gpu.sh" "$WORK_ROOT"
