# ARCIS — Authenticated Robust Coverless Image Signaling

> **Repository continuity note.** This repository was originally created for the project name **NARCIS**. The current protocol and manuscript are named **ARCIS** (*Authenticated Robust Coverless Image Signaling*). The GitHub repository name and the Python package namespace `narcis` are retained for reproducibility and backward compatibility with existing scripts, checkpoints, and result paths.

## Current article

**Title:** *ARCIS: Authenticated Robust Coverless Image Signaling with Finite-Index Feasibility*  
**Target journal:** ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)  
**Status:** submission-ready revision; final author reread pending.

The canonical ACM TOMM snapshot is in [`paper/ACM_TOMM/`](paper/ACM_TOMM/).

Earlier Elsevier/IEEE manuscript files under `paper/` and `paper/IEEE_TMM/` are **historical revisions** and are not the current manuscript.

## Frozen TOMM operating point

The current article freezes the protocol at:

- alphabet size `K = 8`;
- five covers per coded symbol;
- Reed–Solomon parity = 128 bytes;
- BOSSBase 1.01 used for development/operating-point selection;
- Caltech-101 used for externally frozen evaluation;
- five deterministic seeds: `11, 29, 47, 71, 101`.

## Current headline evidence

| Evaluation block | Current TOMM result |
|---|---:|
| BOSSBase development calibration | 1,800 / 1,800 authenticated recoveries |
| BOSSBase index participation | 7,995–8,000 unique covers per seed |
| Caltech-101 external calibration | 1,800 / 1,800 authenticated recoveries |
| Caltech-101 unseen holdouts | 1,163 / 1,200 (96.92%) |
| 12% central crop | 113 / 150; all 37 holdout failures occur here |
| Other seven holdout transformations | 150 / 150 each |
| SRM-lite + ExtraTrees mean macro-AUC | 0.5040 |
| GLCM + logistic-regression mean macro-AUC | 0.5128 |
| 30-head CNN mean macro-AUC | 0.5266 |
| DiffStega frozen UniStega execution | 100 / 100 cases completed |
| DiffStega correct-recovery PSNR | 23.274 dB reproduced vs 23.290 dB published |

These are bounded empirical results for the declared datasets, channel model, operating point, detector protocols, and comparator execution. They do **not** establish universal undetectability, universal robustness, or cross-family numerical superiority.

## ARCIS protocol components

ARCIS combines:

- a learned normalized image descriptor;
- calibration-locked `K=8` quantile codebooks;
- complementary five-cover group banks;
- exact session-balanced keyed Gray mapping;
- AES-GCM authenticated payload/session framing;
- replay control;
- Reed–Solomon correction;
- complete-message finite-index feasibility checks;
- external holdout channel evaluation;
- image-disjoint SRM-lite, GLCM, and CNN selection-detectability audits.

The transmitted natural-image covers remain pixel-unchanged by the sender. Robustness and detectability claims are explicitly limited to the declared protocol and evaluation model.

## Repository layout

- `src/narcis/` — implementation namespace retained from the historical project name;
- `tests/` — unit tests;
- `bossbase_results_rs128_final/`, `bossbase_sensitivity/`, `q1_extension_results/`, `q1_reviewer_results/` — historical/development evidence lineages;
- `paper/ACM_TOMM/` — **current ARCIS/TOMM manuscript snapshot**;
- `paper/IEEE_TMM/` and older `paper/NARCIS*` assets — superseded manuscript revisions;
- `DATASETS.md` — dataset provenance and preparation.

The older result folders remain useful for provenance, but their former `K=16` headline values are **not** the current TOMM operating point. The current aggregate freeze is documented in `FINAL_EXPERIMENTAL_REPORT.md`, `FACT_CHECK.md`, and `paper/ACM_TOMM/REVISION_MANIFEST.md`.

## Installation

Python 3.11 or later is recommended.

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

## Build the ACM TOMM manuscript

A TeX Live installation containing the ACM `acmart` class is required.

```powershell
Set-Location paper/ACM_TOMM
pdflatex ARCIS_TOMM.tex
bibtex ARCIS_TOMM
pdflatex ARCIS_TOMM.tex
pdflatex ARCIS_TOMM.tex
```

The manuscript uses `acmsmall` review mode. Its figures are generated in-source with TikZ/PGFPlots, so no external figure directory is required for the current TOMM build.

## Reproducibility and naming

The repository URL remains:

`https://github.com/EkodeckStephane/NARCIS`

This preserves stable links used during the experimental lineage. **ARCIS is the current method/article name.** The legacy `NARCIS` repository/package names should be interpreted as implementation-history identifiers, not as the current manuscript title.

External datasets and third-party model assets are not redistributed here. See [`DATASETS.md`](DATASETS.md) and the manuscript for provenance and evaluation boundaries.
