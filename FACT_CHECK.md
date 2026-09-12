# ARCIS Fact Check — ACM TOMM Freeze

This audit records the principal claims of the current ARCIS/TOMM manuscript and the frozen values that must remain consistent across the abstract, tables, conclusion, README, and submission metadata.

| Claim | Frozen evidence/value | Status |
|---|---|---|
| Current method name | ARCIS = Authenticated Robust Coverless Image Signaling | Verified against TOMM manuscript |
| Current operating alphabet | `K = 8` | Verified against TOMM manuscript |
| Group size | 5 covers per coded symbol | Verified against TOMM manuscript |
| Reed–Solomon parity | 128 bytes | Verified against TOMM manuscript |
| BOSSBase is development evidence | Operating point fixed before external Caltech evaluation | Verified against TOMM protocol |
| BOSSBase calibration recovery | 1,800/1,800 | Verified against TOMM results freeze |
| BOSSBase cover participation | 7,995–8,000 unique covers per seed | Verified against TOMM results freeze |
| Caltech external calibration recovery | 1,800/1,800 | Verified against TOMM results freeze |
| Caltech index participation | 7,000/7,000 covers used per seed | Verified against TOMM results freeze |
| Caltech unseen holdout recovery | 1,163/1,200 = 96.92% | Verified against TOMM results freeze |
| Holdout failure localization | 37 failures, all in 12% central crop | Verified against TOMM results freeze |
| Seven other holdouts | 150/150 each | Verified against TOMM results freeze |
| 12% central crop | 113/150 | Verified against TOMM results freeze |
| SRM-lite/ExtraTrees mean macro-AUC | 0.5040 | Verified against TOMM detector table |
| GLCM/logistic mean macro-AUC | 0.5128 | Verified against TOMM detector table |
| 30-head CNN mean macro-AUC | 0.5266 | Verified against TOMM detector table |
| DiffStega execution | 100/100 UniStega cases; 700 PNG outputs | Verified against frozen TOMM comparator record |
| DiffStega correct-recovery PSNR | 23.274 dB reproduced; 23.290 dB published | Verified against TOMM comparator table |
| Public repository URL | `https://github.com/EkodeckStephane/NARCIS` | Verified; repository name retained for continuity |
| Current manuscript location | `paper/ACM_TOMM/ARCIS_TOMM.tex` | Verified by repository synchronization |

## Bounded claims

- ARCIS transmits selected natural-image covers without sender-side pixel modification; this alone is not claimed to prove steganographic security.
- The detector results apply to the declared SRM-lite, GLCM, and CNN protocols and their image-disjoint splits.
- The observed 0.5266 CNN macro-AUC is reported as low but measurable selection leakage, not as chance-equivalent universal security.
- The 12% crop failures are retained as an explicit robustness boundary.
- BOSSBase is development evidence; Caltech-101 is the externally frozen evaluation corpus.
- DiffStega is an executable recent comparator under its native reconstruction semantics, not a directly interchangeable capacity/recovery metric.
- Older `K=16`, 1,575/1,575, 3–4 bits/cover and related NARCIS values in historical folders belong to superseded experimental/manuscript lineages and are not headline results of the current TOMM submission.

## Consistency rule

If any final author correction changes one frozen numerical or protocol value, update the manuscript, README, `FINAL_EXPERIMENTAL_REPORT.md`, this fact check, `SESSION_STATUS.md`, and the TOMM revision manifest together before submission.
