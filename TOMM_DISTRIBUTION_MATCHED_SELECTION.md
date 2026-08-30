# NARCIS — Distribution-Matched Selection Protocol

## Status and purpose

This document freezes the next selection redesign before its final detector outcomes are inspected. It was introduced because the earlier hard 12/12 attack-stable pool preserved message robustness but produced a detectable transmitted subset. The hard-stability/IPW result remains diagnostic evidence; it is not promoted as a successful TOMM outcome.

## Development/validation separation

- **Method-development partition:** BOSSBase seed 11.
- The rule below is selected using clean data and the 12 declared calibration attacks on that partition only.
- Final detector results on the remaining BOSSBase partitions and all Caltech-101 partitions are not used to choose the rule.
- Holdout image attacks remain untouched until the rule is locked.
- The CNN and GLCM detector battery is not an optimization objective.

BOSSBase seed 11 may still be reported as a development diagnostic, but it must not be pooled into an independent-validation confidence interval without being labeled accordingly.

## 1. Projection choice

For each partition, generate the already frozen candidate family:

- first 16 principal directions of the clean 64-dimensional descriptor;
- 32 deterministic random directions generated from the partition seed.

For each candidate projection, fit the K=16 quantile codebook on clean embeddings and evaluate label retention on the 12 calibration transformations only.

Rank candidates lexicographically by:

1. maximum worst attack-by-label retention;
2. maximum 5th-percentile attack-by-label retention;
3. maximum mean attack-by-label retention;
4. minimum retention standard deviation;
5. deterministic direction name as final tie-break.

No holdout attack, steganalyzer AUC, semantic category label, or final payload result enters projection selection.

## 2. Clean-only multivariate balance representation

Build a frozen balance representation from the cover index without selection labels:

1. seven native visual statistics already used by NARCIS: mean, standard deviation, horizontal absolute gradient, vertical absolute gradient, entropy, 10th percentile, and 90th percentile;
2. first eight PCA components of the clean 64-dimensional NARCIS descriptor;
3. concatenate the 15 values and standardize them over the complete clean index;
4. partition this representation into **32 K-means strata** using `n_init=20` and random state `20260830 + partition_seed`.

The balance representation uses no attack outcome and no steganalyzer output.

## 3. Reliability

For a cover, define calibration reliability

`r_i = (# calibration attacks retaining its clean K=16 label) / 12`.

Reliability is used only to rank candidate covers inside a clean-only balance stratum. It does not decide stratum quotas.

## 4. Distribution-matched cover scheduler

For every codebook label separately:

1. compute the empirical 32-stratum proportions of **all clean covers assigned to that label**;
2. at each cover request, choose the non-exhausted stratum with the largest proportional deficit relative to this full clean-label distribution;
3. break stratum ties deterministically by HMAC;
4. within the chosen stratum, rank covers by a deterministic HMAC exponential race with weight

   `(0.05 + r_i)^gamma`;

5. select without replacement within the transmission.

Consequently, reliability can change which cover is preferred *inside* a stratum, while the emitted stratum mixture tracks the full clean cover distribution rather than the robust-only subset.

## 5. Session-dependent keyed Gray mapping

The symbol-to-codebook-label Gray mapping is varied deterministically by authenticated sequence number while remaining key dependent. For each session, a cyclic shift and orientation are derived from HMAC material. This preserves the Gray-locality property while preventing fixed framing bits from repeatedly loading the same physical codebook labels across sessions.

The receiver derives the same mapping from the shared key and authenticated session sequence; no additional unauthenticated side information is introduced.

## 6. Calibration-only parameter search

The finite candidate grid is frozen before final validation:

- `gamma ∈ {0, 2, 4, 8, 12}`;
- repetition `∈ {1, 3, 5}`;
- RS parity bytes `∈ {128, 144, 152}`;
- payload sizes `{8, 32, 64}` bytes;
- 10 messages per payload size;
- all 12 calibration attacks.

A configuration is eligible only if:

- every payload preflight is feasible;
- authenticated plaintext recovery is 100% for every calibration attack and every tested payload size.

Among eligible configurations choose deterministically by:

1. minimum mean transmitted covers;
2. minimum RS parity bytes;
3. minimum repetition;
4. minimum gamma.

Detector AUC is not part of this choice.

## 7. Validation gates after lock

After the BOSSBase-seed-11 rule is locked, evaluate without retuning:

1. BOSSBase seeds 29, 47, 71, 101;
2. Caltech-101 seeds 11, 29, 47, 71, 101;
3. real 8/32/64-byte image-channel transmission;
4. untouched holdout attacks;
5. global-statistic logistic detector;
6. residual-feature ExtraTrees detector;
7. selection CNN;
8. four-direction GLCM texture detector.

If the locked rule fails a final validation gate, the failure is retained as evidence. A new redesign requires a new versioned protocol and a fresh validation split; final detector results are never silently recycled into the same optimization loop.

## 8. Evidence policy

All numerical outcomes must be emitted to raw CSV/JSON files before entering the manuscript. The TOMM abstract and conclusion remain frozen until this protocol has completed the validation gates and the claim/code/data audit.