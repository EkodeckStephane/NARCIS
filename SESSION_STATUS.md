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
- ScholarOne metadata: **synchronized to seeded-resampling language**.
- Cover Letter: **synchronized to seeded-resampling language**.
- A4 canonical-lineage workflow: **run 35452993368 in progress**; release remains gated on all five checkpoint SHA checks and canonical result agreement.
- A3 authenticated control-plane manuscript closure: **pending A4 success**.
- Q1 Gate 10: **HOLD until A4 + A3 + final CI + A8 immutable release**.
- Senior Reviewer prescreen: **HOLD on the same release-control items**.

The branch remains a release candidate until these checks are completed.
