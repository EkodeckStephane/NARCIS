# NARCIS — Complementary Triplet Selection Protocol

## Purpose

This document freezes the next TOMM selection rule after the development-partition analysis showed that individual reliability weighting could preserve robustness while still leaving a detectable intra-stratum bias.

The method below is fixed **before** inspecting BOSSBase seeds 29/47/71/101 or any Caltech-101 result produced with this rule.

## Development partition

Only BOSSBase seed 11 is used for method development.

The calibration-locked projection procedure remains unchanged. On the fresh seed-11 checkpoint it selects `random_14` at `K=16`.

## Frozen parameters

- codebook size: `K=16`;
- calibration attacks: the existing 12-attack calibration set;
- repetition: `3`;
- Reed–Solomon parity: `128` bytes;
- clean distribution representation: 7 native image statistics + 8 PCA scores of the clean 64-dimensional descriptor;
- standardization: calibration/index clean data only;
- distribution strata: 32 K-means strata using seed `20260828 + partition_seed`;
- secret-dependent ordering: HMAC-derived, with the authenticated sequence included in the mapping/selection context.

No steganalyzer output, holdout attack result, or final-detector AUC is used to choose any of these values.

## Failure masks

For each indexed cover, define a 12-bit calibration failure mask. Bit `a` equals one exactly when the attacked image is assigned a different codebook label from the clean image under calibration attack `a`.

For repetition three, a triplet has a correct majority for every calibration attack exactly when no attack is failed by two members of the triplet. Equivalently, if the three failure masks are `F1`, `F2`, and `F3`, the admissibility conditions are

```text
F1 & F2 = 0
F1 & F3 = 0
F2 & F3 = 0
```

This permits individually imperfect covers to be combined so that their failure modes are complementary.

## Distribution-preserving triplet construction

For every requested codebook label:

1. candidate covers are restricted to that clean label;
2. the target stratum proportions are the natural stratum proportions among all indexed covers carrying that label;
3. the first, second, and third cover are selected by the largest current proportional stratum deficit, with an HMAC rank as deterministic secret-dependent tie-break;
4. the second cover must have a failure mask disjoint from the first;
5. the third cover must have a failure mask disjoint from the union of the first two;
6. covers are not reused within one transmission;
7. covers may reappear in another authenticated sequence because the HMAC context changes with the sequence and protected payload.

There is no scalar reliability weight and no detector-trained selection objective.

## Frozen evaluation protocol

### Robustness

For plaintext lengths 8, 32, and 64 bytes, use 10 independently encrypted messages per length. Report actual AES-GCM authenticated plaintext recovery after the image-channel labels, majority vote, RS decoding, framing/CRC, and AEAD verification.

### Detectability

The primary operational detectability unit is one authenticated transmission/session. For every session, selected covers are compared against covers sampled from the remainder of the same frozen index. The initial detector battery comprises:

- 7 global native statistics + logistic regression;
- residual/SRM-lite features + ExtraTrees;
- 4-direction GLCM texture features + logistic regression;
- selection CNN.

Multiple independent detector splits/initializations must be reported.

A cumulative-support analysis may also be reported as a secondary diagnostic, but it is not the primary detectability measure. After many secret-dependent sessions, almost the entire finite index can appear at least once; treating every cover ever used as one positive class and the small never-used remainder as the negative class measures cumulative support exposure rather than the detectability of a transmitted session.

## Seed-11 post-freeze observations

After the rule above was fixed, the development partition produced:

- 30/30 feasible transmissions for 8/32/64-byte plaintexts;
- 360/360 authenticated recoveries over the 30 messages × 12 calibration attacks;
- zero RS corrections on those calibration trials because the complementary triplets produced the intended majority label directly;
- mean session-level global-statistic AUC approximately 0.507 across 30 sessions with repeated splits;
- mean session-level clean-15D logistic AUC approximately 0.509 across the same sessions.

These detector results are validation observations, not inputs to the selection rule.

## Transfer gate

The exact rule above must now be applied without retuning to BOSSBase seeds 29/47/71/101 and then to all five Caltech-101 partitions. Any partition that fails feasibility, authenticated recovery, or detectability must be reported rather than repaired by partition-specific tuning.
