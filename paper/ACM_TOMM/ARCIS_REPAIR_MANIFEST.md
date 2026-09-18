# ARCIS TOMM final synchronization manifest

Historical executable TOMM base: `b8ee42d547b580b9e1639de559b1dfa6ea88d4ef`.

Restored/synchronized:
- group-bank implementation and projection;
- exact session-balanced mapping;
- TOMM validation runner and detector tooling;
- TOMM-specific unit tests;
- `tomm_results/rs_parity_ablation_summary.json`;
- `tomm_results/communication_cost.json`;
- `tomm_results/finite_index_blocking_risk.json`;
- ARCIS/TOMM manuscript identity, metadata, checklist and Q1 audit.

Headline freeze:
- calibration 1800/1800;
- holdout 1163/1200 = 96.92%;
- RS0 → RS128: 829/1200 → 1163/1200;
- mean images/session 970 → 2676.7;
- RS128 8/32/64 B: 2320 / 2640 / 3070 images;
- detector macro-AUC 0.504 / 0.513 / 0.527.

Final author-package PDF SHA-256: `2db5b0d5014367807407ecd8c105fe2a1ea21a4087bb2497b524c84afce41b0c`.
