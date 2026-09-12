# ARCIS Final Experimental Report — ACM TOMM Freeze

This document records the aggregate numerical freeze used by the current ACM TOMM manuscript. Earlier NARCIS/K=16 reports remain part of the development history but are superseded for the current article.

## Operating point and evaluation separation

| Item | Frozen value |
|---|---|
| Alphabet | `K = 8` |
| Covers per coded symbol | 5 |
| Reed–Solomon parity | 128 bytes |
| Seeds | 11, 29, 47, 71, 101 |
| Development corpus | BOSSBase 1.01 |
| External corpus | Caltech-101 |
| Caltech training/index per seed | 1,500 / 7,000 image-disjoint images |
| Calibration transformations | 12 |
| Unseen holdout transformations | 8 |

The operating point was fixed from BOSSBase development evidence before the externally frozen Caltech-101 campaign.

## Development evidence — BOSSBase

- 1,800/1,800 authenticated calibration recoveries across five seeds.
- 7,995–8,000 unique covers exercised per seed.
- The development lineage uses the same `K=8`, group-size-5, RS128 construction subsequently frozen for external validation.

## External calibration — Caltech-101

- 1,800/1,800 authenticated recoveries.
- All 7,000 indexed covers are exercised in every partition.
- Maximum reported Reed–Solomon correction demand in calibration: 37 byte positions.

## External unseen holdouts — Caltech-101

- Overall: **1,163/1,200 authenticated recoveries (96.92%)**.
- Seven holdout transformations: **150/150 each**.
- Unseen 12% central crop: **113/150**.
- All 37 holdout failures occur in the 12% crop condition.
- The observed maximum correction demand reaches the 64-byte correction radius in the strongest holdout regime.

The 12% crop is therefore reported as an empirical channel boundary rather than hidden by an average robustness claim.

## Final selection-detectability audit

| Detector | Mean macro-AUC | Reported mean |
|---|---:|---:|
| SRM-lite + ExtraTrees | 0.5040 | 0.504 |
| GLCM + logistic regression | 0.5128 | 0.513 |
| 30-head CNN | 0.5266 | 0.527 |

The CNN value describes a low but measurable selected-vs.-remainder signal under the declared audit. It is not evidence of universal detectability or undetectability.

## DiffStega frozen reproduction

- Official upstream commit: `73cd7cb8d102f4fc0f5bb168a71cfb948077d89a`.
- UniStega cases executed: 100/100.
- Generated PNG outputs: 700.
- Independently reproduced correct-recovery PSNR: **23.274 dB**.
- Value reported in the DiffStega paper: **23.290 dB**.

ARCIS and DiffStega have different communication semantics. ARCIS evaluates authenticated finite-index byte signaling with unchanged indexed natural images; DiffStega evaluates secret-image reconstruction through a generative diffusion pipeline. Metrics are therefore kept family-specific.

## Claim boundaries

The current evidence supports the declared finite-index feasibility, authenticated recovery, channel-robustness, index-usage, and selection-detectability claims at the frozen operating point. It does not support claims of universal robustness, universal undetectability, maximum capacity, or direct numerical superiority across different coverless/generative families.

## Canonical manuscript snapshot

The current article and its submission metadata are in `paper/ACM_TOMM/`. Historical result folders and older manuscript revisions remain in the repository for provenance but must not be substituted for this TOMM freeze when quoting headline results.
