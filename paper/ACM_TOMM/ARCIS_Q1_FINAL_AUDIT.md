# ARCIS — Final Q1 / Senior Reviewer Audit after D1--D7

Target: **ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)**  
Manuscript: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**

## Gate result
**Gate 10: PASS for the current evidence-bounded manuscript.**  
**Senior Reviewer prescreen: PASS.**

The central claims are supported by released code/results and by the final D1--D7 closure. The manuscript now separates whole-message authenticated recovery from heterogeneous SOTA robustness metrics, uses paired inference for the RS study, uses five external partitions rather than overlapping splits as the detector inference unit, quantifies the communication/traffic side channel, makes finite-index sufficiency explicit, and attributes the cyclic balancing invariant to the session shift rather than to Gray ordering.

## Remaining reviewer-sensitive points
The current RS128 operating point is traffic-intensive, and this is now a quantified deployment result rather than an implicit cost. External image-domain evidence consists of BOSSBase development plus Caltech-101 validation. Guo--Ping remains the closest natural-image-selection comparator, but the published robustness percentage is kept under its native recovery semantics rather than treated as equivalent to ARCIS exact authenticated whole-message success.

These points define future generalization and deployment work; they no longer create unsupported central claims in the manuscript.

## Validation
- D2 final-schedule classical detector workflow: **PASS**, all five partition jobs.
- TOMM source validation: **PASS**, unit tests, preflight and ACM LaTeX compilation.
- Defensive-phrase scan on manuscript/cover/metadata: **PASS**.
