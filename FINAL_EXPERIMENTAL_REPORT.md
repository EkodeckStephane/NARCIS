# ARCIS Final Experimental Report — ACM TOMM Freeze

## Frozen operating point
`K=8`, five covers/coded symbol, RS128; BOSSBase development and five image-disjoint Caltech-101 external partitions.

## External results
- Calibration: **1,800/1,800** authenticated recoveries.
- Holdout: **1,163/1,200 (96.92%)**.
- Seven holdouts: 150/150 each.
- 12% crop: 113/150; all 37 failures occur there.

## Controlled RS-parity ablation
| RS | Successes/1,200 | Success | Mean images/session |
|---:|---:|---:|---:|
| 0 | 829 | 69.08% | 970.0 |
| 32 | 1,064 | 88.67% | 1,396.7 |
| 64 | 1,115 | 92.92% | 1,825.0 |
| 96 | 1,145 | 95.42% | 2,250.0 |
| 128 | 1,163 | 96.92% | 2,676.7 |

## RS128 communication cost
8 B = 2,320 images (0.0276 bit/image); 32 B = 2,640 (0.0970); 64 B = 3,070 (0.1668).

## Conditional finite-index blocking model
Under the declared i.i.d.-uniform multinomial planning model: 8 B = 5.04e-43, 32 B = 1.64e-34, 64 B = 1.14e-25. These are analytical planning values, not cryptographic guarantees.

## Detectability
SRM-lite 0.5040; GLCM 0.5128; CNN 0.5266 mean macro-AUC. The CNN result is low but measurable selection leakage under the declared warden.
