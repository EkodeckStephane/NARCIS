# ARCIS TOMM synchronization manifest

Historical executable TOMM base: `b8ee42d547b580b9e1639de559b1dfa6ea88d4ef`.

Recorded fresh Caltech checkpoint campaign: `bdef888c90d191550a1e3ae29ec25b4a2d422e66`.

Current repair/release branch: `arcis-a1-a10-repair`.

## Restored and synchronized
- group-bank implementation and projection;
- exact session-balanced mapping;
- authenticated metadata and replay-control path;
- TOMM validation runner and detector tooling;
- TOMM-specific unit tests;
- RS-parity and communication-cost summaries;
- finite-index blocking-risk analysis;
- seeded Caltech resampling-overlap analysis;
- ARCIS/TOMM manuscript identity, metadata, checklist, Cover Letter and Q1 audit;
- dependence-aware detector and parity reporting.

## Manuscript-facing freeze
- calibration **1,800/1,800**;
- holdout **1,163/1,200 = 96.92%**;
- RS0 → RS128: **829/1,200 → 1,163/1,200**;
- paired endpoint: **334 gains / 0 losses**, descriptive;
- mean images/session **970 → 2,676.7**;
- RS128 8/32/64 B: **2,320 / 2,640 / 3,070 images**;
- detector mean AUC **0.5040 / 0.5128 / 0.5266** with descriptive resampling ranges.

## Release-control gate
A4 workflow **35452993368** must regenerate all five fresh checkpoints, match the recorded SHA-256 values, and reproduce the canonical manuscript-facing channel results before A3 manuscript closure and A8 release.

No final PDF/package hash or immutable release identifier is recorded here until the release-candidate head has passed all final checks.
