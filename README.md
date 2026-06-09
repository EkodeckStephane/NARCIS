# NARCIS

**NARCIS** stands for **Neural Adaptive Robust Coverless Image Signaling**.
It is an authenticated selection-based coverless protocol that communicates
through unchanged natural images selected from a shared, attack-qualified
index.

## Main Results

The evaluation uses five partitions each of BOSSBase and RGB Caltech-101:

- 1,575 clean, calibration, and holdout message-condition trials;
- `1,575 / 1,575` complete authenticated message recoveries;
- 98.74% and 98.59% mean symbol accuracy;
- 3-4 bits/cover on BOSSBase and 4 bits/cover on every Caltech-101 partition;
- selection-CNN AUCs of 0.515 and 0.530, with both 95% intervals including
  0.5.

These results are bounded to the released protocol, datasets, attack suite,
parameters, and detector classes. They do not establish universal
undetectability or maximum nominal capacity.

## Components

- self-supervised channel-invariant image descriptor;
- balanced quantile codebook;
- multi-attack cover qualification;
- finite-index protected-message feasibility test;
- HMAC-derived keyed Gray symbol assignment;
- AES-GCM payload and metadata protection;
- replay rejection and CRC framing;
- configurable Hamming and Reed-Solomon correction;
- calibrated and holdout JPEG, noise, blur, resize, crop, and rotation tests;
- global-statistic, residual-feature, and CNN selection detectors.

## Repository Layout

- `src/narcis/`: protocol implementation;
- `tests/`: unit tests;
- `run_bossbase_campaign.py`: principal BOSSBase campaign;
- `download_caltech101.py`: resumable Caltech-101 preparation;
- `consolidate_q1_extension.py`: cross-dataset evidence and figures;
- `run_bossbase_sensitivity.py`: dimension, loss-weight, and projection study;
- `bossbase_results_rs128_final/`: consolidated principal results;
- `bossbase_sensitivity/`: consolidated sensitivity results;
- `q1_extension_results/`: consolidated cross-dataset and CNN evidence;
- `paper/`: Elsevier manuscript, figures, cover letter, and review reports.

External datasets and trained checkpoints are intentionally not committed.
See [`DATASETS.md`](DATASETS.md) for dataset provenance and preparation.

## Installation

Python 3.11 or later is recommended.

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

## Principal Campaign

Download BOSSBase 1.01 separately, then run:

```powershell
python run_bossbase_campaign.py `
  --dataset-root "C:\path\to\BOSSbase" `
  --output bossbase_results `
  --seeds 11,29,47,71,101 `
  --train-count 2000 `
  --index-count 8000 `
  --epochs 5 `
  --messages 10 `
  --payload-bytes 8 `
  --rs-parity 128 `
  --model-size 128 `
  --embedding-dim 64
```

The full campaign is CPU-intensive because 12 calibration attacks are applied
to each 8,000-image index at native resolution.

For Caltech-101, run `download_caltech101.py`, then invoke the campaign with
`--input-mode RGB --channel-size 256 --train-count 1500 --index-count 7000`.

## Manuscript

The compiled article is available at
[`paper/NARCIS.pdf`](paper/NARCIS.pdf). To rebuild it:

```powershell
Set-Location paper
pdflatex NARCIS.tex
bibtex NARCIS
pdflatex NARCIS.tex
pdflatex NARCIS.tex
```

## Availability

The repository provides the implementation, deterministic seeds, attack
definitions, consolidated CSV/JSON evidence, manuscript source, and figures.
Dataset redistribution follows the original dataset providers' terms.
