# Final Experimental Report

## Evaluation Scope

NARCIS is evaluated on two natural-image corpora with five deterministic
partitions each:

| Dataset | Channel representation | Train/index | Messages/seed | Trials |
|---|---|---:|---:|---:|
| BOSSBase 1.01 | Native 512 x 512 grayscale | 2,000 / 8,000 | 10 | 1,050 |
| Caltech-101 | Centre-fitted 256 x 256 RGB | 1,500 / 7,000 | 5 | 525 |

Both campaigns use five training epochs, 12 calibration attacks, eight
holdout strengths, the clean channel, eight-byte plaintexts, and 128
Reed-Solomon parity bytes.

## End-to-End Results

| Metric | BOSSBase | Caltech-101 |
|---|---:|---:|
| Authenticated recoveries | 1,050 / 1,050 | 525 / 525 |
| Mean symbol accuracy | 98.7368% | 98.5857% |
| Worst symbol accuracy | 81.6092% | 79.8851% |
| Maximum corrected byte positions | 61 | 63 |
| Feasible bits/cover | 3-4 | 4 on every seed |

The unseen 12% crop was the hardest condition on both datasets. The unseen
9-degree rotation was the second most difficult condition.

## Selection Detectability

| Dataset | Global logistic | Residual ExtraTrees | Selection CNN |
|---|---:|---:|---:|
| BOSSBase | 0.518 [0.489, 0.547] | 0.514 [0.486, 0.543] | 0.515 [0.463, 0.566] |
| Caltech-101 | 0.531 [0.504, 0.557] | 0.533 [0.504, 0.562] | 0.530 [0.481, 0.579] |

The two classical Caltech-101 detectors identify a small dataset-specific
selection shift. The CNN intervals include 0.5 on both datasets. These are
bounded detector results, not a universal undetectability claim.

## Ablation and Sensitivity

Removing attack qualification reduced controlled CIFAR-100 message success
from 100% to 43.65%. Equal VICReg-style loss weights retained fewer stable
covers than the 25/25/1 configuration. A 128-dimensional descriptor retained
more covers in the reduced study but did not improve full-protocol capacity or
reliability. Alternative projection directions can outperform PC1 in retained
cover fraction; PC1 is used as a deterministic variance-maximising choice.

## Reproducibility

Consolidated evidence is stored in:

- `bossbase_results_rs128_final/`;
- `bossbase_sensitivity/`;
- `q1_extension_results/`;
- `paper/figures/`.

The graphical abstract is available as
`paper/figures/graphical_abstract.pdf` and `.png`.
