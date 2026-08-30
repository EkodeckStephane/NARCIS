# NARCIS — Full-Corpus Uniform Robust Selection Freeze

## Purpose

This document freezes a distribution-preserving redesign before its experimental outcomes are inspected. It is motivated by the observation that a hard 12/12 attack-stable eligibility subset can remain statistically distinguishable even after inverse-probability weighting.

## Principle

The revised candidate protocol removes the attack-qualified *sub-pool* from the transmission support. Every indexed cover remains eligible. Robustness is moved from eligibility filtering to projection choice plus coding redundancy.

This makes distribution preservation structural: for a fixed quantile label, HMAC sampling is uniform over the complete label bucket rather than over an attack-stable subset.

## Projection choice

For each frozen dataset partition, evaluate the same candidate family used by the TOMM revision:

- up to 16 principal directions;
- 32 deterministic random unit directions generated from seed `20260828 + partition_seed`.

For each candidate direction:

1. fit a K=16 quantile codebook on clean index embeddings;
2. obtain clean labels;
3. for each of the 12 calibration attacks, obtain attacked labels;
4. compute the label-retention rate separately for every attack × clean-label cell.

Rank directions lexicographically by:

1. maximum **minimum attack×label retention rate**;
2. maximum 5th percentile attack×label retention;
3. maximum mean attack×label retention;
4. minimum standard deviation of attack×label retention;
5. deterministic direction name tie break.

No holdout attack, payload success result, detector AUC, semantic category, or steganalysis output may enter this projection choice.

## Cover selection

For the selected projection:

- all covers remain eligible;
- each K=16 label bucket contains the full clean quantile bucket;
- per-cover sampling weights are exactly 1;
- the existing payload-dependent HMAC exponential-race ordering is retained, which becomes a keyed pseudorandom permutation under equal weights;
- no stability threshold, propensity weight, semantic class label, detector score, MMD score, or GLCM score is used to rank covers.

Dataset identifiers used in the HMAC must be canonical dataset-relative identifiers, not machine-specific absolute paths.

## Coding search

Calibration search is restricted to:

- repetition `r ∈ {1, 3, 5, 7, 9, 11}`;
- Reed–Solomon parity `p ∈ {128, 144, 152}` bytes;
- plaintext payload sizes `{8, 32, 64}` bytes;
- 10 deterministic encrypted messages per payload size and partition.

For a candidate `(r,p)`, evaluate all 12 calibration channel transformations.

Selection rule for the operating point:

1. require 100% authenticated plaintext recovery over all calibration trials used for tuning;
2. among passing candidates, minimize mean transmitted covers;
3. then minimize repetition;
4. then minimize parity.

Detector performance is not a tuning criterion.

If no candidate passes, this full-corpus uniform design is rejected and a new versioned experiment must be preregistered before inspecting holdout outcomes.

## Validation gates after freeze

Once the operating point is selected:

1. evaluate all declared holdout attacks without changing projection/coding;
2. evaluate support-level and traffic-level detectability;
3. run global-statistics logistic, residual ExtraTrees, selection CNN, and GLCM detectors using frozen repetition/split rules;
4. repeat on all predefined BOSSBase and Caltech-101 partitions;
5. retain any adverse result rather than suppressing it.

## Scientific interpretation

Passing this experiment would replace “distribution-preserving qualification” with a stronger formulation: **full-corpus distribution-preserving cover selection with calibration-locked robust codebooks and coding redundancy**. Failing it would establish that robustness cannot be moved entirely out of eligibility filtering at acceptable overhead under the current descriptor/channel model.
