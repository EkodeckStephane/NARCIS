# ARCIS

**ARCIS** stands for **Authenticated Robust Cover-Selection Image Signaling**. The repository keeps its historical GitHub name (`NARCIS`) to preserve stable URLs and provenance; the current scientific identity and ACM TOMM manuscript are **ARCIS**.

Current manuscript: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**.

## Current TOMM evidence

- External calibration: **1,800/1,800** authenticated recoveries.
- External holdout: **1,163/1,200 (96.92%)**; all 37 failures occur under the 12% central crop.
- Detector mean macro-AUC: **0.504 / 0.513 / 0.527** for SRM-lite / GLCM / CNN.
- Controlled RS sweep: **829/1,200 (RS0)**, **1,064/1,200 (RS32)**, **1,115/1,200 (RS64)**, **1,145/1,200 (RS96)**, **1,163/1,200 (RS128)**.
- Mean transmitted images/session: **970 → 2,676.7** from RS0 to RS128.
- RS128 8/32/64-byte sessions require **2,320 / 2,640 / 3,070** images.
- Conditional finite-index blocking risk at RS128: approximately **5.04e-43 / 1.64e-34 / 1.14e-25** for 8 / 32 / 64 bytes under the declared i.i.d.-uniform planning model.

The high carrier count is an explicit operational limitation.

## Canonical implementation

The executable TOMM lineage originates at commit `b8ee42d547b580b9e1639de559b1dfa6ea88d4ef`. The current main branch restores and synchronizes the group-bank implementation, exact session-balanced mapping, TOMM runner, detector tooling, tests, and manuscript-facing results.

Key paths:
- `src/narcis/group_bank.py`
- `src/narcis/group_bank_protocol.py`
- `src/narcis/group_bank_projection.py`
- `src/narcis/protocol.py`
- `run_tomm_groupbank_cached.py`
- `tomm_results/`
- `paper/ACM_TOMM/`

## Claim boundaries

ARCIS does **not** claim universal undetectability, universal robustness, traffic-analysis resistance, or direct numerical superiority over generative steganography. DiffStega is retained only as secondary contextual/executable positioning evidence under different semantics.

Older NARCIS/Signal Processing/IEEE-TMM/`K=16` materials remain historical provenance only.
