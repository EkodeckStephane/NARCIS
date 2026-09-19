# ARCIS Fact Check — ACM TOMM release candidate

| Item | Current value |
|---|---|
| Name | ARCIS = Authenticated Robust Cover-Selection Image Signaling |
| Title | ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints |
| K / group / final RS | 8 / 5 / 128 |
| External design | five seeded Caltech-101 train--index resamplings; within-run training/index disjoint; cross-seed image pools overlap |
| External calibration | 1,800/1,800 |
| External holdout | 1,163/1,200 = 96.92% |
| 12% crop | 113/150; all 37 failures |
| RS0/32/64/96/128 | 829 / 1,064 / 1,115 / 1,145 / 1,163 successes |
| RS0→RS128 paired endpoint | 334 gains / 0 losses; descriptive under repeated attacks and overlapping resamplings |
| Mean images/session | 970 → 2,676.7 |
| RS128 images for 8/32/64 B | 2,320 / 2,640 / 3,070 |
| SRM-lite mean / resampling range | 0.5040 / 0.5014–0.5052 |
| GLCM mean / resampling range | 0.5128 / 0.5120–0.5138 |
| CNN mean / resampling range | 0.5266 / 0.5232–0.5301 |
| Detector interpretation | 20 image-disjoint repeated splits quantify within-resampling stability; five resampling means are descriptive, not independent external replications |
| Cyclic mapping property | exact balancing follows from the session shift; Gray order fixes symbol ordering |
| Repository | https://github.com/EkodeckStephane/NARCIS |
| Current repair/release branch | arcis-a1-a10-repair |
| A4 canonical-lineage run | GitHub Actions 35452993368; release remains gated on all five SHA checks and canonical result agreement |

Historical K=16 / 1,575/1,575 / 3–4 bits-per-cover values are superseded for the current TOMM submission.
