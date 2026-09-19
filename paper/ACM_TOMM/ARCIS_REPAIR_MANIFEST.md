# ARCIS TOMM synchronization manifest

Historical executable TOMM base: `b8ee42d547b580b9e1639de559b1dfa6ea88d4ef`.

Recorded fresh Caltech checkpoint campaign: `bdef888c90d191550a1e3ae29ec25b4a2d422e66`.

Repair provenance branch: `arcis-a1-a10-repair`.

Validated scientific submission snapshot: `main` commit `254f31e7c44e43f104509c117b0efb4c414dcdcd`.

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
- detector mean AUC **0.5040 / 0.5128 / 0.5266** with descriptive resampling ranges;
- authenticated control plane **150/150** metadata roundtrips with **5/5** tamper, replay and wrong-receiver rejections.

## Canonical A4 closure
**PASS.** The archived checkpoint bundle `NARCIS_TOMM_FRESH_CHECKPOINTS.zip` has SHA-256 `8193bb8462d5b79fb18462e8e55091b8982752161ed388e95b7b7785483ed1f1`. All five Caltech checkpoint members exactly match the SHA-256 values recorded in `TOMM_FRESH_CAMPAIGN.md`. The canonical holdout aggregate has SHA-256 `27f99fa00e9e8a7f1792195799615e8c8235718fa613fc20476a9f6014c70fcf` and reproduces the frozen 1,163/1,200 result.

The attempted September 19 retraining used a different runtime from the archived campaign and is retained only as a diagnostic; it is not substituted for the byte-identical canonical checkpoints.

## A8 submission closure
**CLOSED.** The repaired scientific state was merged to `main` at `254f31e7c44e43f104509c117b0efb4c414dcdcd`, and TOMM revision validation run `35460375489` completed **SUCCESS**. No GitHub release is required for the current TOMM submission. Tag/release creation is deferred until acceptance, when the publication version is frozen.
