# ARCIS

**ARCIS** stands for **Authenticated Robust Cover-Selection Image Signaling**.
The repository keeps its historical GitHub name (`NARCIS`) to preserve existing URLs and provenance, but the current ACM TOMM manuscript and frozen external-validation lineage use the name **ARCIS**.

ARCIS is a selection-based coverless signaling protocol that transmits unchanged natural images from a finite shared index. The frozen TOMM construction combines a learned normalized image descriptor, a calibration-locked `K=8` quantile codebook, complementary five-cover group banks, exact session-balanced keyed Gray mapping, AES-GCM authenticated framing and replay control, and Reed-Solomon error correction.

## Current ACM TOMM evidence

The final development operating point was fixed on BOSSBase before external validation on five image-disjoint Caltech-101 partitions.

- External calibration: **1,800 / 1,800** authenticated message recoveries.
- External holdout: **1,163 / 1,200 (96.92%)** authenticated recoveries across eight unseen transformations.
- The **37 holdout failures are all in the 12% central-crop condition**; each of the other seven holdouts achieves 150/150 recoveries.
- Final selection-detectability audit: mean macro-AUC **0.504** (SRM-lite/ExtraTrees), **0.513** (GLCM/logistic regression), and **0.527** (30-head CNN).
- Every external 7,000-image cover index is exercised by the frozen 30-session schedule.

### Reed-Solomon parity ablation

A controlled parity sweep keeps the learned representation, codebook-selection rule, and complementary group banks fixed and changes only the RS parity budget. Across the same 1,200 external holdout trials:

| RS parity bytes | Authenticated recoveries | Success rate | Mean transmitted images/session |
|---:|---:|---:|---:|
| 0 | 829 / 1,200 | 69.08% | 970.0 |
| 32 | 1,064 / 1,200 | 88.67% | 1,396.7 |
| 64 | 1,115 / 1,200 | 92.92% | 1,825.0 |
| 96 | 1,145 / 1,200 | 95.42% | 2,250.0 |
| 128 | 1,163 / 1,200 | 96.92% | 2,676.7 |

The sweep makes the reliability/communication tradeoff explicit rather than treating RS128 as cost-free.

### Communication cost at the frozen RS128 point

| Plaintext | Coded groups | Transmitted images | Useful payload bits/image |
|---:|---:|---:|---:|
| 8 B | 464 | 2,320 | 0.0276 |
| 32 B | 528 | 2,640 | 0.0970 |
| 64 B | 614 | 3,070 | 0.1668 |

These values include authenticated encryption, framing, RS128 coding, 3-bit symbolization, and the five-cover majority group. They are intentionally reported as an operational limitation of the present construction.

### Finite-index feasibility and blocking-risk model

For a realized protected session, complete emission is feasible exactly when the demand for every mapped label does not exceed the number of available groups for that label.

For planning only, the repository also contains an explicitly conditional i.i.d.-uniform symbol-demand model. With a balanced 7,000-image external index (`K=8`, 875 covers/label, five covers/group, 175 groups/label), the resulting exact blocking probabilities are approximately:

- 8 B: `5.04e-43`
- 32 B: `1.64e-34`
- 64 B: `1.14e-25`

These probabilities are conditional on the stated multinomial idealization; they are not presented as a cryptographic theorem or an empirical independence result.

## Reproducibility lineage

The historical TOMM implementation is frozen at commit:

`b8ee42d547b580b9e1639de559b1dfa6ea88d4ef`

It contains the exact complementary group-bank implementation, signature-balanced keyed scheduler, session-balanced Gray mapping, external-validation runner, detector workflows, tests, and DiffStega reproduction tooling used to establish the evidence lineage.

Key implementation files include:

- `src/narcis/group_bank.py`
- `src/narcis/group_bank_projection.py`
- `src/narcis/group_bank_protocol.py`
- `src/narcis/protocol.py`
- `src/narcis/benchmark.py`
- `run_tomm_groupbank_cached.py`

The repair branch `arcis-tomm-gemini-repair` is the manuscript/artifact synchronization branch. New TOMM-facing machine-readable evidence is stored under `tomm_results/`.

## Claim boundaries

ARCIS does **not** claim universal undetectability, universal robustness, traffic-analysis resistance, or direct numerical superiority over generative steganography. DiffStega is retained as secondary executable positioning evidence under its native secret-image reconstruction semantics. The central claim is the implemented finite-index authenticated signaling construction and its measured reliability, communication cost, feasibility, and detector-scoped security behavior under the declared channel and warden models.

## Installation

Python 3.11 or later is recommended.

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
```

External datasets and trained checkpoints are intentionally not committed. See `DATASETS.md` for dataset provenance and preparation.
