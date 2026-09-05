#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIFFSTEGA_ROOT="${1:?Usage: run_diffstega_metrics_frozen.sh <DiffStega-root> [metrics-output]}"
METRICS_OUTPUT="${2:-$(dirname "$DIFFSTEGA_ROOT")/evidence/metrics}"
ENV_ROOT="${DIFFSTEGA_ENV_ROOT:-$ROOT/.micromamba}"
MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-$ROOT/.mamba-root}"
export MAMBA_ROOT_PREFIX

if [[ ! -x "$ENV_ROOT/bin/micromamba" ]]; then
  mkdir -p "$ENV_ROOT/bin"
  curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest \
    | tar -xj -C "$ENV_ROOT/bin" --strip-components=1 bin/micromamba
fi

if [[ ! -d "$MAMBA_ROOT_PREFIX/envs/diffstega-metrics" ]]; then
  "$ENV_ROOT/bin/micromamba" create -y -n diffstega-metrics -c conda-forge python=3.11.5 pip
fi

MM=("$ENV_ROOT/bin/micromamba" run -n diffstega-metrics)
"${MM[@]}" python -m pip install --upgrade 'pip<25'
"${MM[@]}" python -m pip install --index-url https://download.pytorch.org/whl/cu121 \
  torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0
"${MM[@]}" python -m pip install -r "$ROOT/tools/diffstega_metrics_requirements.txt"

mkdir -p "$METRICS_OUTPUT"
"${MM[@]}" python "$ROOT/tools/evaluate_diffstega_outputs.py" \
  --diffstega-root "$DIFFSTEGA_ROOT" \
  --output "$METRICS_OUTPUT" \
  --device auto

sha256sum "$METRICS_OUTPUT"/* | sort > "$METRICS_OUTPUT/artifact_sha256.txt"
echo "Frozen DiffStega metrics written to $METRICS_OUTPUT"
