# ARCIS

**ARCIS** stands for **Authenticated Robust Cover-Selection Image Signaling**. The repository keeps its historical GitHub name (`NARCIS`) to preserve stable URLs and provenance; the current scientific identity and ACM TOMM manuscript are **ARCIS**.

Current manuscript: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**.

## Current TOMM evidence

- External calibration: **1,800/1,800** authenticated recoveries.
- External holdout: **1,163/1,200 (96.92%)**; all 37 failures occur under the 12% central crop.
- RS-parity sweep: **829 / 1,064 / 1,115 / 1,145 / 1,163** successes out of 1,200 at RS0/32/64/96/128.
- Exact paired RS0→RS128 comparison: **334 gains / 0 losses**, reported descriptively because attacks repeat within sessions and the five Caltech resamplings overlap.
- Mean transmitted images/session: **970 → 2,676.7** from RS0 to RS128.
- RS128 8/32/64-byte sessions require **2,320 / 2,640 / 3,070** images.
- Conditional finite-index blocking risk at RS128: approximately **5.04e-43 / 1.64e-34 / 1.14e-25** for 8 / 32 / 64 bytes under the stated i.i.d.-uniform planning model.
- Detector means across five seeded Caltech train--index resamplings: **0.5040 / 0.5128 / 0.5266** for SRM-lite / GLCM / CNN.
- Canonical A5 ablation: **1,163 / 1,042 / 1,160 / 1,166 / 1,038** successes for full ARCIS / random groups / uniform scheduler / fixed mapping / matched bucket baseline.
- Guo–Ping 2026 primary-source audit: published native maximum-capacity robustness **99.54% / 98.64% / 97.19%** at **10 / 14 / 15 bits** on Holidays / VOC / ImageNet; retained under its own per-segment recovery semantics.
- Descriptive resampling ranges: **0.5014–0.5052 / 0.5120–0.5138 / 0.5232–0.5301**. The five resamplings are not treated as independent external replications.

The communication-cost analysis identifies carrier volume and session-volume observability as the principal deployment constraints of the current operating point. The manuscript discusses fixed-volume batching, padding, dummy covers, timing shaping, denser group signaling, and adaptive parity allocation as direct extension paths.

## Canonical implementation

The executable TOMM lineage originates at commit `b8ee42d547b580b9e1639de559b1dfa6ea88d4ef`. The validated TOMM submission snapshot is commit `c3e58a157b0b3bfe58959436e2d02e46d09c40cb` on `main`, validated by GitHub Actions run `35455852993` (**SUCCESS**). The former `arcis-a1-a10-repair` branch is retained only as repair provenance.

A GitHub tag/release is **not a TOMM submission gate** for ARCIS. Version freezing by tag/release is deferred to the post-acceptance publication stage.

Key paths:
- `src/narcis/group_bank.py`
- `src/narcis/group_bank_protocol.py`
- `src/narcis/group_bank_projection.py`
- `src/narcis/protocol.py`
- `run_tomm_groupbank_cached.py`
- `tomm_results/rs_parity_ablation_summary.json`
- `tomm_results/detector_resampling_summary.json`
- `tomm_results/caltech_resampling_overlap.json`
- `tomm_results/communication_cost.json`
- `tomm_results/finite_index_blocking_risk.json`
- `tomm_results/A5_CANONICAL_COMPONENT_ABLATION.json`
- `tomm_results/GUO_PING_2026_SOURCE_AUDIT.json`
- `paper/ACM_TOMM/`

## Evaluation scope

ARCIS evaluates authenticated whole-plaintext recovery from a finite shared natural-image index, image-content selection discrimination under residual, texture, and learned wardens, and session-volume observability through measured cover counts. Recent cover-selection and generative approaches are positioned under their native information objects and recovery semantics so that heterogeneous percentages are not treated as a common performance scale.

Older NARCIS / Signal Processing / IEEE-TMM / `K=16` materials remain historical provenance only.
