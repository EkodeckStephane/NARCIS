# ARCIS A5 — Canonical component-ablation closure

**Status: CLOSED / PASS.**

A5 was rerun against the byte-identified A4 canonical Caltech lineage, not against the earlier noncanonical A1–A10 workflow checkpoints. The full ARCIS arm reproduces the canonical holdout result exactly: **1,163/1,200 (96.92%)**, with per-seed recoveries **240, 214, 240, 231, 238**.

## Matched canonical ablation

| Variant | Authenticated recovery | ARCIS-only gains / reverse gains | Interpretation |
|---|---:|---:|---|
| ARCIS full | 1,163/1,200 (96.92%) | reference | full construction |
| Random groups | 1,042/1,200 (86.83%) | 121 / 0 | complementary qualified grouping is a major robustness contributor |
| Uniform group scheduler | 1,160/1,200 (96.67%) | 10 / 7 | scheduling refinement is not claimed as a major standalone recovery gain |
| Fixed symbol-to-cluster mapping | 1,166/1,200 (97.17%) | 3 / 6 | recovery is similar/slightly higher, but balancing is substantially degraded |
| Matched bucket baseline | 1,038/1,200 (86.50%) | 125 / 0 | group-bank communication unit materially improves crop robustness |

The paired counts are descriptive because attacks repeat within sessions and the five Caltech resamplings overlap.

The attack-level diagnosis localizes the difference: all variants recover 150/150 for Gaussian, blur, and rotation holdouts. Under 8% crop, ARCIS remains 150/150 versus 132/150 for random groups and 126/150 for the matched bucket baseline. Under 12% crop, ARCIS reaches 113/150 versus 10/150 and 12/150 respectively.

The cyclic session mapping is justified by **balance rather than a recovery advantage**. Fixed mapping gives 1,166/1,200 recoveries, but its mean label-emission coefficient of variation is **0.1314**, versus **0.0225** for ARCIS, and each coded symbol visits only one visual cluster instead of all eight over a complete cycle.

## Comparator scope

The complete Guo–Ping 2026 primary source has now been audited. It fixes the PZM/SA-PQE/clustering/representative-selection chain and the published parameters (N=18), (J=128), (Delta=40), and ((w_{center},w_{stab})=(0.7,0.3)). It also defines robustness as per-representative message-segment recovery and reports 99.54%, 98.64%, and 97.19% at 10, 14, and 15 bits on Holidays, VOC, and ImageNet, respectively.

The paper still does not freeze several choices required for a bit-identical independent implementation: scalar treatment of complex PZM coefficients before modulo quantization, a common image-resampling rule, K-means initialization/restarts/random seed, exact attack-library interpolation/RNG choices, and the identities of the selected 50,000 ImageNet images. The manuscript therefore uses Guo–Ping's published numbers directly under their native semantics and records these limits in `GUO_PING_2026_REPRODUCIBILITY_AUDIT.md`, rather than presenting a completed implementation as if it were the authors' exact executable system. DiffStega remains executable positioning evidence in its distinct secret-image generative regime.

Machine-readable evidence:
- `tomm_results/A5_CANONICAL_COMPONENT_ABLATION.json`
- `tomm_results/A5_CANONICAL_PAIRED_DESCRIPTIVE.json`
- `tools/a5_cached_component_ablation.py`
- `tools/verify_a5_component_ablation.py`

Primary-source audit:
- `tomm_results/GUO_PING_2026_SOURCE_AUDIT.json`
- `paper/ACM_TOMM/GUO_PING_2026_REPRODUCIBILITY_AUDIT.md`
