# Final Experimental Report

## Principal Protocol

The principal NARCIS campaign uses BOSSBase 1.01:

- 10,000 grayscale images at native `512 x 512` resolution;
- five deterministic partitions;
- 2,000 descriptor-training images and 8,000 index images per partition;
- five training epochs;
- ten encrypted eight-byte messages per partition;
- 12 calibration attacks and eight holdout strengths plus the clean channel;
- Reed-Solomon coding with 128 parity bytes.

Channel transformations are applied at native resolution. Images are resized
to `128 x 128` only at the encoder boundary.

## End-to-End Results

| Metric | Result |
|---|---:|
| Message-condition trials | 1,050 |
| Successful authenticated recoveries | 1,050 |
| Message success | 100% |
| Mean symbol accuracy | 98.7368% |
| Worst individual symbol accuracy | 81.6092% |
| Maximum corrected byte positions | 61 |

The most difficult condition was the unseen 12% central crop, with 84.37%
mean symbol accuracy. The unseen 9-degree rotation produced 91.75%.

## Feasible Operating Points

| Seed | Alphabet | Bits/cover | Stable fraction | Minimum bucket |
|---:|---:|---:|---:|---:|
| 11 | 16 | 4 | 35.29% | 92 |
| 29 | 16 | 4 | 30.38% | 61 |
| 47 | 8 | 3 | 48.73% | 177 |
| 71 | 16 | 4 | 33.59% | 80 |
| 101 | 16 | 4 | 35.58% | 99 |

The net plaintext rate is 0.184 bits/cover at four bits/cover and 0.138
bits/cover at three bits/cover for the tested short messages.

## Selection Detectability

| Detector | Mean AUC | 95% interval |
|---|---:|---:|
| Seven-feature logistic regression | 0.518 | [0.489, 0.547] |
| 52-feature residual ExtraTrees | 0.514 | [0.486, 0.543] |

Both intervals include chance performance. This result is specific to the
tested selection detectors and is not a universal steganalysis claim.

## Sensitivity

The targeted reduced experiment supports stronger invariance and variance
weights over equal weighting. A 128-dimensional descriptor retained more
stable covers in the reduced subset but did not improve capacity or reliability
in a two-seed full-protocol check. Alternative scalar projection directions
occasionally retained more covers than PC1; PC1 is therefore a deterministic
maximum-variance choice, not a stability optimum.

## Reproducibility

The consolidated evidence is stored in:

- `bossbase_results_rs128_final/`;
- `bossbase_sensitivity/`;
- `paper/figures/`.

Unit-test status at publication: `18 passed`.
