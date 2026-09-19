# ARCIS Fact Check — ACM TOMM submission snapshot

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
| A3 control plane | 150/150 roundtrips; 5/5 tamper, 5/5 replay, 5/5 wrong-receiver rejections |
| A4 checkpoint bundle SHA-256 | 8193bb8462d5b79fb18462e8e55091b8982752161ed388e95b7b7785483ed1f1 |
| A4 canonical holdout SHA-256 | 27f99fa00e9e8a7f1792195799615e8c8235718fa613fc20476a9f6014c70fcf |
| A4 status | PASS: all five canonical Caltech checkpoint SHA-256 values match the fresh-campaign record; holdout = 1,163/1,200 |
| A5 canonical component ablation | full 1,163/1,200; random groups 1,042; uniform scheduler 1,160; fixed mapping 1,166; matched bucket 1,038 |
| A5 mechanism interpretation | complementary qualified grouping carries the principal recovery effect; fixed mapping is recovery-similar but worsens label-emission CV from 0.0225 to 0.1314 |
| Guo–Ping 2026 native comparator | 10/14/15 bits; 99.54/98.64/97.19% mean native robustness on Holidays/VOC/ImageNet; per-representative segment recovery, not authenticated whole-message recovery |
| Cyclic mapping property | exact balancing follows from the session shift; Gray order fixes symbol ordering |
| Repository | https://github.com/EkodeckStephane/NARCIS |
| Validated submission snapshot | `main` commit `c3e58a157b0b3bfe58959436e2d02e46d09c40cb` |
| Final TOMM validation | run `35455852993` — SUCCESS |
| A8 | **CLOSED for TOMM submission** |
| Post-acceptance freeze | tag/release deferred until acceptance; not a current submission requirement |

Historical K=16 / 1,575/1,575 / 3–4 bits-per-cover values are superseded for the current TOMM submission.
