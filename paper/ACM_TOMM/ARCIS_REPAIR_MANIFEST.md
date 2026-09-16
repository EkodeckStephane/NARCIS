# ARCIS TOMM Repair Manifest

## Scientific lineage

- Repository: `EkodeckStephane/NARCIS`
- Historical TOMM implementation commit: `b8ee42d547b580b9e1639de559b1dfa6ea88d4ef`
- Repair branch: `arcis-tomm-gemini-repair`
- Current article name: **ARCIS — Authenticated Robust Cover-Selection Image Signaling**
- Current title: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**

The historical implementation commit is retained as the exact executable lineage for the external-validation protocol. The repair branch adds manuscript-facing evidence and consistency material without changing the interpretation of those historical runs.

## Verified implementation components at the historical TOMM commit

- `src/narcis/group_bank.py`: complementary five-cover bank construction and calibration majority-failure optimization.
- `src/narcis/group_bank_projection.py`: calibration-locked projection selection.
- `src/narcis/group_bank_protocol.py`: signature-balanced keyed group scheduling and within-session no-cover-reuse enforcement.
- `src/narcis/protocol.py`: exact cyclic session-balanced keyed Gray mapping and protocol encode/decode path.
- `src/narcis/benchmark.py`: deterministic 8/32/64-byte external workload and nonce discipline.
- `run_tomm_groupbank_cached.py`: frozen external-validation execution path.

## Added machine-readable repair evidence

- `tomm_results/rs_parity_ablation_summary.json`
- `tomm_results/communication_cost.json`
- `tomm_results/finite_index_blocking_risk.json`

## Frozen experimental values used by the repaired manuscript

### External validation

- Calibration: `1800/1800` authenticated recoveries.
- Holdout: `1163/1200` authenticated recoveries (`96.92%`).
- RS128 holdout failures: `37`, all under central crop 12%.
- Mean detector macro-AUC: SRM-lite `0.504`, GLCM `0.513`, CNN `0.527`.

### Reed-Solomon parity ablation

| RS parity bytes | Successes / 1200 | Success rate | Mean images/session |
|---:|---:|---:|---:|
| 0 | 829 | 69.08% | 970.0 |
| 32 | 1064 | 88.67% | 1396.7 |
| 64 | 1115 | 92.92% | 1825.0 |
| 96 | 1145 | 95.42% | 2250.0 |
| 128 | 1163 | 96.92% | 2676.7 |

### RS128 communication accounting

| Plaintext | Coded groups | Images | Useful bits/image |
|---:|---:|---:|---:|
| 8 B | 464 | 2320 | 0.027586 |
| 32 B | 528 | 2640 | 0.096970 |
| 64 B | 614 | 3070 | 0.166775 |

### Conditional finite-index blocking model

For a balanced 7000-cover external index with `K=8`, group size 5, and `175` groups per label, the conditional i.i.d.-uniform demand model gives:

- 8 B (`m=464`): approximately `5.04e-43`
- 32 B (`m=528`): approximately `1.64e-34`
- 64 B (`m=614`): approximately `1.14e-25`

These are planning-model probabilities, not empirical independence results and not cryptographic security guarantees.

## Claim boundaries

The repaired paper does not claim:

- universal steganographic undetectability;
- traffic-analysis resistance;
- production deployment;
- universal channel robustness;
- cross-family numerical superiority over DiffStega or other generative methods;
- that AES-GCM or Reed-Solomon themselves are novel contributions.

The principal contribution is the implemented finite-index authenticated cover-selection signaling construction and its bounded empirical/formal characterization.

## Q1 closure

`ARCIS_Q1_FINAL_AUDIT.md` records the final gate assessment. Gate 10 is PASS for the scientific package under the bounded claims. Final author-side portal confirmations remain outside the scientific closure.
