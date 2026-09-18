# ARCIS Fact Check — ACM TOMM D1--D7 Freeze

| Item | Current value |
|---|---|
| Name | ARCIS = Authenticated Robust Cover-Selection Image Signaling |
| Title | ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints |
| K / group / final RS | 8 / 5 / 128 |
| External calibration | 1,800/1,800 |
| External holdout | 1,163/1,200 = 96.92% |
| 12% crop | 113/150; all 37 failures |
| RS0/32/64/96/128 | 829 / 1,064 / 1,115 / 1,145 / 1,163 successes |
| Exact RS0→RS128 McNemar | 334 gains / 0 losses; (p=5.71\times10^{-101}) |
| Mean images/session | 970 → 2,676.7 |
| RS128 images for 8/32/64 B | 2,320 / 2,640 / 3,070 |
| SRM-lite partition mean / CI95 | 0.5040 / [0.5021, 0.5060] |
| GLCM partition mean / CI95 | 0.5128 / [0.5119, 0.5138] |
| CNN partition mean / CI95 | 0.5266 / [0.5230, 0.5302] |
| Detector inference unit | five external partitions; 20 repeated splits/partition are stability diagnostics |
| Cyclic mapping property | exact balancing follows from the session shift; Gray order fixes symbol ordering |
| Repository | https://github.com/EkodeckStephane/NARCIS |
| D1--D7 repair branch | arcis-tomm-d1-d7 |

Historical K=16 / 1,575/1,575 / 3–4 bits-per-cover values are superseded for the current TOMM submission.
