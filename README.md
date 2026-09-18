# ARCIS

**ARCIS** stands for **Authenticated Robust Cover-Selection Image Signaling**. The repository keeps its historical GitHub name (`NARCIS`) to preserve stable URLs and provenance; the current scientific identity and ACM TOMM manuscript are **ARCIS**.

Current manuscript: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**.

## Current TOMM evidence

- External calibration: **1,800/1,800** authenticated recoveries.
- External holdout: **1,163/1,200 (96.92%)**; all 37 failures occur under the 12% central crop.
- RS-parity sweep: **829 / 1,064 / 1,115 / 1,145 / 1,163** successes out of 1,200 at RS0/32/64/96/128.
- Exact paired RS0→RS128 comparison: **334 gains / 0 losses**, exact McNemar (p=5.71\times10^{-101}).
- Mean transmitted images/session: **970 → 2,676.7** from RS0 to RS128.
- RS128 8/32/64-byte sessions require **2,320 / 2,640 / 3,070** images.
- Conditional finite-index blocking risk at RS128: approximately **5.04e-43 / 1.64e-34 / 1.14e-25** for 8 / 32 / 64 bytes under the stated i.i.d.-uniform planning model.
- Final partition-level detector means: **0.5040 / 0.5128 / 0.5266** for SRM-lite / GLCM / CNN.
- Five-partition 95% intervals: **0.5021–0.5060 / 0.5119–0.5138 / 0.5230–0.5302**.

The communication-cost analysis identifies carrier volume and session-volume observability as the principal deployment constraints of the current operating point. The manuscript discusses fixed-volume batching, padding, dummy covers, timing shaping, denser group signaling, and adaptive parity allocation as direct extension paths.

## Canonical implementation

The executable TOMM lineage originates at commit `b8ee42d547b580b9e1639de559b1dfa6ea88d4ef`. The D1--D7 scientific closure is frozen on branch `arcis-tomm-d1-d7`.

Key paths:
- `src/narcis/group_bank.py`
- `src/narcis/group_bank_protocol.py`
- `src/narcis/group_bank_projection.py`
- `src/narcis/protocol.py`
- `run_tomm_groupbank_cached.py`
- `tomm_results/rs_parity_ablation_inference.json`
- `tomm_results/detector_hierarchical_inference.json`
- `paper/ACM_TOMM/`

## Evaluation scope

ARCIS evaluates authenticated whole-plaintext recovery from a finite shared natural-image index, image-content selection discrimination under residual, texture, and learned wardens, and session-volume observability through measured cover counts. Recent cover-selection and generative approaches are positioned under their native information objects and recovery semantics so that heterogeneous percentages are not treated as a common performance scale.

Older NARCIS / Signal Processing / IEEE-TMM / `K=16` materials remain historical provenance only.
