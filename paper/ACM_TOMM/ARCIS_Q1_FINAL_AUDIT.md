# ARCIS — Q1 / Senior Reviewer release-candidate audit

Target: **ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)**  
Manuscript: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**

## Gate result
**Gate 10: HOLD until canonical-lineage closure and immutable release.**  
**Senior Reviewer prescreen: HOLD on the same release-control items.**

The manuscript-facing recovery, communication-cost, finite-index, and detector claims have been rewritten to respect the actual dependence structure. The five Caltech runs are seeded train--index resamplings of one corpus and are not treated as independent external replications. RS gain/loss counts are descriptive because attacks repeat within sessions. Detector means and resampling ranges are likewise descriptive.

## Active closure items
- **A4 canonical lineage:** GitHub Actions run **35452993368** regenerates the five recorded Caltech checkpoints, verifies their SHA-256 hashes, reruns the authenticated channel, and recomputes the component ablations. A4 closes only if all five hashes match and the manuscript-facing canonical recovery totals remain consistent.
- **A3 authenticated control plane:** the executable recheck performs authenticated metadata roundtrips for all sessions and explicit tamper/replay negative tests. The manuscript integration is finalized only after the canonical A4 run succeeds.
- **Editorial synchronization:** ScholarOne metadata and the Cover Letter now use the seeded-resampling interpretation and no longer report independence-based five-run confidence intervals.
- **A8 release:** main merge, immutable tag/release, and final release audit occur only after the preceding items pass.

## Reviewer-sensitive scope
The RS128 operating point remains traffic-intensive and is reported as a measured deployment constraint. External image-domain evidence consists of BOSSBase development plus Caltech-101 validation through overlapping seeded resamplings. Guo--Ping remains the closest natural-image-selection comparator, but source-paper robustness is kept under its native recovery semantics rather than treated as equivalent to ARCIS exact authenticated whole-message success.

No final PASS is recorded in this file before the canonical A4 manifests and final release status are verified.
