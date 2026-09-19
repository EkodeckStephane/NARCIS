# ARCIS Session Status

- Current name: **ARCIS — Authenticated Robust Cover-Selection Image Signaling**.
- Current title: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**.
- Target: **ACM TOMM**.
- Frozen protocol: `K=8`, group size 5, final RS128.
- External design: five seeded Caltech-101 train--index resamplings; training/index sets are disjoint within each run, while cross-seed index pools overlap.
- External calibration: **1,800/1,800**.
- External holdout: **1,163/1,200 (96.92%)**.
- RS ablation: **829 / 1,064 / 1,115 / 1,145 / 1,163** successes at RS0/32/64/96/128.
- RS0→RS128 paired endpoint: **334 gains / 0 losses**, reported descriptively.
- Mean images/session: **970 → 2,676.7**.
- RS128 8/32/64-byte image counts: **2,320 / 2,640 / 3,070**.
- Detector means across the five resamplings: **0.5040 / 0.5128 / 0.5266**, with descriptive ranges **0.5014–0.5052 / 0.5120–0.5138 / 0.5232–0.5301**.
- Direction E′ cyclic-mapping clarification: **integrated**.
- **A3 CLOSED:** 150/150 authenticated metadata roundtrips; 5/5 tamper, replay, and wrong-receiver rejections; manuscript, ScholarOne, and Cover Letter synchronized.
- **A4 CLOSED:** canonical archive `NARCIS_TOMM_FRESH_CHECKPOINTS.zip` SHA-256 `8193bb8462d5b79fb18462e8e55091b8982752161ed388e95b7b7785483ed1f1`; all five Caltech checkpoint SHA-256 values match the recorded fresh campaign; canonical holdout aggregate SHA-256 `27f99fa00e9e8a7f1792195799615e8c8235718fa613fc20476a9f6014c70fcf` and reproduces 1,163/1,200 with the frozen per-seed results.
- Non-identical retraining under a different runtime is retained only as a diagnostic and is not substituted for the canonical checkpoint bytes.
- **A5 CLOSED:** canonical component ablation reproduces ARCIS at 1,163/1,200; random groups 1,042/1,200; uniform scheduler 1,160/1,200; fixed mapping 1,166/1,200; matched bucket 1,038/1,200. Complementary qualified groups carry the main recovery effect; cyclic mapping is justified primarily by balance (label-emission CV 0.0225 vs 0.1314 with fixed mapping).
- Guo–Ping 2026: complete primary source audited; native maximum-capacity robustness = 99.54% / 98.64% / 97.19% at 10 / 14 / 15 bits on Holidays / VOC / ImageNet, under per-representative segment semantics.
- ScholarOne metadata: **CLOSED / synchronized**.
- Cover Letter: **CLOSED / synchronized**.
- **A8 CLOSED for TOMM submission:** repair branch merged to `main` at `254f31e7c44e43f104509c117b0efb4c414dcdcd`; TOMM revision validation run `35460375489` completed **SUCCESS**.
- GitHub tag/release: **deferred to post-acceptance version freezing; not a submission blocker**.
- Q1 Gate 10: **PASS** — static claim/code/data verifier PASS and rendered-PDF inspection PASS; CI run `35465970002` completed SUCCESS.

The validated scientific submission snapshot is the cited `main` commit. Later documentation-only commits do not replace that experimental lineage.
