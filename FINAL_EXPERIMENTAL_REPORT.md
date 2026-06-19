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
selection shift. The five-partition CNN interval includes 0.5, but 20 repeated
fits on seed 47 give 0.533 [0.517, 0.548]. This is a weak matched-index
selection leak, not evidence of universal undetectability.

## Ablation and Sensitivity

Removing attack qualification reduced controlled CIFAR-100 message success
from 100% to 43.65%. The matched BOSSBase seed-11 ablation fell from 210/210
to 142/210 recoveries without qualification. A calibration-locked direction
search increased the minimum stable bucket from 92 to 161 and recovered
210/210 targeted trials. This single-partition result does not replace the
five-seed PC1 campaign.

With 128 Reed-Solomon parity symbols per block and `K=16`, the implemented net
rate is 0.184, 0.646, and 1.213 bits/cover for 8-, 32-, and 128-byte
plaintexts. The 128-byte case spans two RS blocks.

## Reproducibility

Consolidated evidence is stored in:

- `bossbase_results_rs128_final/`;
- `bossbase_sensitivity/`;
- `q1_extension_results/`;
- `q1_reviewer_results/`;
- `paper/figures/`.

The graphical abstract is available as
`paper/Graphical_Abstract.tex`, `.pdf`, and `.png`.
