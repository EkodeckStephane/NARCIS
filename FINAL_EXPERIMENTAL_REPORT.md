# ARCIS Final Experimental Report — ACM TOMM D1--D7 Freeze

## Frozen operating point
`K=8`, five covers/coded symbol, RS128; BOSSBase development and five image-disjoint Caltech-101 external partitions.

## External recovery
- Calibration: **1,800/1,800** authenticated recoveries.
- Holdout: **1,163/1,200 (96.92%)**.
- Seven holdout transformations: **150/150** each.
- 12% crop: **113/150**; all 37 holdout failures occur there.

## Paired RS-parity ablation
| RS | Recovery | Exact 95% CI | Mean images/session | Gain/loss vs previous |
|---:|---:|---:|---:|---:|
| 0 | 829/1,200 (69.08%) | 66.38–71.69% | 970.0 | — |
| 32 | 1,064/1,200 (88.67%) | 86.74–90.41% | 1,396.7 | 235/0 |
| 64 | 1,115/1,200 (92.92%) | 91.32–94.30% | 1,825.0 | 51/0 |
| 96 | 1,145/1,200 (95.42%) | 94.08–96.53% | 2,250.0 | 30/0 |
| 128 | 1,163/1,200 (96.92%) | 95.77–97.82% | 2,676.7 | 18/0 |

All four adjacent exact McNemar contrasts remain significant after Holm adjustment. The RS0→RS128 endpoint has **334 gains / 0 losses**, exact (p=5.71\times10^{-101}).

## Communication and traffic observability
At RS128:
- 8 B → 2,320 images → 0.0276 useful bit/image.
- 32 B → 2,640 images → 0.0970 useful bit/image.
- 64 B → 3,070 images → 0.1668 useful bit/image.

The cover count therefore exposes payload-length-class information in an unshaped session. The manuscript treats fixed-volume batching, payload padding, dummy-cover insertion, timing shaping, denser group signaling, and adaptive parity as deployment extensions.

## Conditional finite-index planning
Under the stated i.i.d.-uniform coded-symbol planning model:
- 8 B: (5.04\times10^{-43})
- 32 B: (1.64\times10^{-34})
- 64 B: (1.14\times10^{-25})

The realized-session feasibility criterion remains (d_k\le a_k) for every label, with necessity and sufficiency stated label by label.

## Hierarchical detector audit
Inference uses the **five external partition means**; the 20 image-disjoint repetitions within a partition characterize split stability.

| Detector | Mean AUC | Between-partition SD | Partition range | 95% CI (n=5) |
|---|---:|---:|---:|---:|
| SRM-lite + ExtraTrees | 0.5040 | 0.0015 | 0.5014–0.5052 | 0.5021–0.5060 |
| GLCM + logistic | 0.5128 | 0.0007 | 0.5120–0.5138 | 0.5119–0.5138 |
| 30-head CNN | 0.5266 | 0.0029 | 0.5232–0.5301 | 0.5230–0.5302 |

## SOTA positioning
Guo--Ping and ARCIS are positioned through their native quantitative regimes and recovery-event definitions. ARCIS success is exact authenticated whole-plaintext recovery after majority decoding, RS correction, framing, and AES-GCM verification. Guo--Ping's published robustness percentages remain under the source paper's native robustness metric and are not placed on a common percentage scale with ARCIS.
