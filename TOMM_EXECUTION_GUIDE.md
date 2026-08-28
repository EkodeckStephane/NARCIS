# NARCIS — ACM TOMM Execution Guide

This guide defines the exact execution path for the fresh TOMM validation campaign. It is intentionally separated from the manuscript so that experimental choices are frozen before the new outcomes are inspected.

## 1. Required assets

The repository intentionally does not redistribute BOSSBase, Caltech-101, or trained encoder checkpoints.

### BOSSBase 1.01

Expected by default under:

```text
dataset_external/BOSSbase/
```

The campaign requires at least 10,000 discoverable images because each fixed seed allocates 2,000 images to representation training and 8,000 disjoint images to the cover index.

### Caltech-101

Expected by default under:

```text
dataset_external/caltech101/images/
```

The campaign requires at least 8,500 discoverable images because each fixed seed allocates 1,500 images to representation training and 7,000 disjoint images to the cover index. The previously used Caltech-101 corpus contains enough images for this split.

### Optional historical encoder checkpoints

When the exact historical checkpoints are available, place or point to:

```text
bossbase_results/encoder_seed_11.pt
bossbase_results/encoder_seed_29.pt
bossbase_results/encoder_seed_47.pt
bossbase_results/encoder_seed_71.pt
bossbase_results/encoder_seed_101.pt

caltech101_results/encoder_seed_11.pt
caltech101_results/encoder_seed_29.pt
caltech101_results/encoder_seed_47.pt
caltech101_results/encoder_seed_71.pt
caltech101_results/encoder_seed_101.pt
```

Alternative directories can be supplied with `--boss-checkpoints` and `--caltech-checkpoints`.

If the historical checkpoints are unavailable, the fresh campaign must retrain the encoders from the datasets with `--epochs 5`. The manuscript must then describe the TOMM campaign as a fresh retraining rather than as reuse of the IEEE-era models.

## 2. Environment

Recommended Python version: 3.11.

Install the repository dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the complete unit-test suite before scientific execution:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
```

A GPU-capable PyTorch environment is recommended for retraining and repeated CNN detectability evaluation. CPU execution is supported by the code but the full ten-partition campaign is computationally intensive.

## 3. Mandatory preflight

Before any scientific run:

```powershell
$env:PYTHONPATH = "src"
python run_tomm_validation.py --stage preflight --output tomm_results
```

Inspect:

```text
tomm_results/preflight.json
```

A dataset is `ready=true` only when the required image count is present and either all five checkpoints are available or a positive retraining epoch count has been requested.

### Preflight for fresh retraining

```powershell
python run_tomm_validation.py `
  --stage preflight `
  --epochs 5 `
  --output tomm_results
```

## 4. Frozen principal campaign

Seeds:

```text
11, 29, 47, 71, 101
```

Payloads:

```text
8, 32, 64 plaintext bytes
```

Default codebook target:

```text
K = 16
```

Reed–Solomon parity:

```text
128 parity bytes
```

Projection search:

```text
16 principal directions + 32 deterministic random directions
```

Detector repetitions:

```text
20 independent train/test/training repetitions per partition
```

Detector families:

1. global-statistic logistic regression;
2. residual-feature ExtraTrees;
3. selection CNN;
4. GLCM texture detector.

The projection is selected from clean + calibration information only. Holdout attacks and detector AUCs are excluded from projection selection.

### Reuse exact historical checkpoints

```powershell
python run_tomm_validation.py `
  --stage all `
  --epochs 0 `
  --seeds 11,29,47,71,101 `
  --payload-sizes 8,32,64 `
  --messages 10 `
  --clusters 16 `
  --rs-parity 128 `
  --detector-repeats 20 `
  --output tomm_results
```

### Fresh five-epoch retraining

```powershell
python run_tomm_validation.py `
  --stage all `
  --epochs 5 `
  --seeds 11,29,47,71,101 `
  --payload-sizes 8,32,64 `
  --messages 10 `
  --clusters 16 `
  --rs-parity 128 `
  --detector-repeats 20 `
  --output tomm_results
```

## 5. Outputs that must exist before manuscript rewrite

For every dataset and seed:

```text
projection_candidates.csv
projection_choice.json
payload_raw.csv
payload_summary.csv
detectability_repetitions.csv
timing.json
```

Dataset-level consolidation:

```text
selected_projections.csv
payload_raw_all_seeds.csv
payload_summary_all_seeds.csv
detectability_all_seeds.csv
```

No abstract, conclusion, highlight, cover letter, or comparative claim is updated from the TOMM campaign until these files exist and pass the claim/code/data audit.

## 6. Result acceptance gates

### T1 — Distribution preservation

Report standardized mean-difference diagnostics before and after weighting, effective sample size, and all detector AUC distributions. A result is not described as undetectable merely because one detector is near chance.

### T2 — Projection generalization

Report the selected direction and minimum stable bucket independently for all ten frozen partitions. The old BOSSBase seed-11 `random_15` result is historical evidence, not a substitute for this multi-seed run.

### T3 — Real payload channel

For 8, 32, and 64 bytes, report actual transmitted-cover count, per-condition symbol accuracy, RS corrections, and exact authenticated plaintext recovery. Analytical rate extrapolation is not accepted as an image-channel experiment.

### T4 — Detectability

Report all detector repetitions and uncertainty. If any detector produces a reproducible advantage above chance, retain that result and revise the selection mechanism only through a new versioned experiment; do not suppress or relabel it.

### T5 — External comparison

Run the frozen DiffStega baseline protocol in `TOMM_BASELINE_PROTOCOL.md`. Guo–Ping 2026 remains literature-level context unless a faithful validated implementation becomes available.

### T6 — Submission audit

Every numerical statement in manuscript, tables, figures, supplementary material, cover letter, and highlights must map to a versioned CSV/JSON field or a deterministic derivation script.

## 7. ACM TOMM manuscript build

The review manuscript is under:

```text
paper/ACM_TOMM/NARCIS_TOMM.tex
```

Build after the scientific results have been frozen:

```powershell
Set-Location paper/ACM_TOMM
pdflatex NARCIS_TOMM.tex
bibtex NARCIS_TOMM
pdflatex NARCIS_TOMM.tex
pdflatex NARCIS_TOMM.tex
```

The review source uses ACM's `manuscript` mode. Production formatting must be left to ACM/TAPS rather than manually forcing journal margins or typography.

## 8. Provenance record

Before final submission, record:

- Git commit SHA of NARCIS;
- SHA-256 hashes or provider identifiers for dataset archives where redistribution permits only provenance rather than inclusion;
- checkpoint hashes;
- Python/PyTorch/CUDA versions;
- hardware identifier;
- full command line;
- start/end timestamps;
- all raw CSV/JSON outputs;
- external baseline repository commit and model identifiers.

This record becomes the authoritative evidence package for the TOMM manuscript.
