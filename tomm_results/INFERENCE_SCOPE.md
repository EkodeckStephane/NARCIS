# ARCIS inference-scope note

The current ACM TOMM manuscript does **not** treat the 1,200 holdout outcomes or the five Caltech train--index runs as independent inferential units.

Canonical manuscript-facing files:
- `rs_parity_ablation_summary.json`
- `detector_resampling_summary.json`
- `caltech_resampling_overlap.json`
- `communication_cost.json`
- `finite_index_blocking_risk.json`

The older files `rs_parity_ablation_inference.json` and `detector_hierarchical_inference.json` are retained only as historical analysis artifacts. Their independence-based confidence/significance calculations are superseded by the current dependence-aware reporting: parity recoveries and paired gain/loss counts are descriptive, and detector means/ranges across the five overlapping Caltech resamplings are descriptive.

This note prevents historical inference artifacts from being mistaken for the current manuscript's statistical claims.
