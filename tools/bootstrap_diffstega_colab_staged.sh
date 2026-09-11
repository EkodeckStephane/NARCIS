#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_ROOT="${1:-/content/drive/MyDrive/NARCIS_DiffStega_Work}"
ENV_ROOT="${DIFFSTEGA_ENV_ROOT:-$ROOT/.micromamba}"
MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-$ROOT/.mamba-root}"
export MAMBA_ROOT_PREFIX

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo 'No NVIDIA runtime detected. In Colab choose Runtime > Change runtime type > GPU.' >&2
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
  'numpy<2' diffusers==0.26.3 accelerate==0.23.0 transformers==4.38.2 \
  controlnet_aux==0.0.7 huggingface_hub==0.20.3 gdown==5.2.0

"${MM[@]}" python - <<'PY'
import json, sys, torch
state={
 'python':sys.version,
 'torch':torch.__version__,
 'cuda_available':torch.cuda.is_available(),
 'cuda_runtime':torch.version.cuda,
 'device_count':torch.cuda.device_count(),
 'devices':[torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
}
print(json.dumps(state,indent=2))
if sys.version_info[:3] != (3,11,5): raise SystemExit('Python freeze mismatch')
if torch.__version__.split('+')[0] != '2.1.0': raise SystemExit('PyTorch freeze mismatch')
if not torch.cuda.is_available(): raise SystemExit('CUDA unavailable')
PY

"${MM[@]}" bash "$ROOT/tools/prepare_diffstega_frozen_gpu.sh" "$WORK_ROOT"

echo "STAGED_PREPARED"
echo "WORK_ROOT=$WORK_ROOT"
echo "MAMBA_ROOT_PREFIX=$MAMBA_ROOT_PREFIX"
