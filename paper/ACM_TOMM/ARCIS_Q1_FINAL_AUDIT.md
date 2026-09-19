# ARCIS — Q1 / Senior Reviewer submission audit

Target: **ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)**  
Manuscript: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**

## Gate result
**A3: CLOSED.**  
**A4: CLOSED on the archived canonical lineage.**  
**A8: CLOSED for TOMM submission.** The repair branch was merged to `main` at `c3e58a157b0b3bfe58959436e2d02e46d09c40cb`, and TOMM revision validation run `35455852993` completed **SUCCESS**.

A GitHub tag/release is not treated as a current submission gate. Immutable version freezing is deferred to the post-acceptance publication stage.

**Gate 10 is not declared PASS here solely from A3/A4/A8 closure.** Any other A1–A10 item that remains partial must be resolved or explicitly accepted before the global gate is changed.

The manuscript-facing recovery, communication-cost, finite-index, and detector claims respect the actual dependence structure. The five Caltech runs are seeded train--index resamplings of one corpus and are not treated as independent external replications. RS gain/loss counts are descriptive because attacks repeat within sessions. Detector means and resampling ranges are likewise descriptive.

## Closed items in this repair
- **A4 canonical lineage:** the archived `NARCIS_TOMM_FRESH_CHECKPOINTS.zip` has SHA-256 `8193bb8462d5b79fb18462e8e55091b8982752161ed388e95b7b7785483ed1f1`. Its five Caltech checkpoints match the SHA-256 values recorded by campaign commit `bdef888c90d191550a1e3ae29ec25b4a2d422e66`. The canonical holdout aggregate has SHA-256 `27f99fa00e9e8a7f1792195799615e8c8235718fa613fc20476a9f6014c70fcf` and yields 1,163/1,200 overall with per-seed successes 240, 214, 240, 231, and 238.
- **A3 authenticated control plane:** the implementation completes 150/150 metadata roundtrips across five seeds and rejects 5/5 tested tamper cases, 5/5 immediate replays, and 5/5 wrong-receiver cases. The evidence is frozen in `tomm_results/A3_AUTHENTICATED_CONTROL_PLANE_AUDIT.json` and integrated in the manuscript.
- **Editorial synchronization:** ScholarOne metadata and the Cover Letter use the seeded-resampling interpretation, contain the A3 evidence, and do not report independence-based five-run confidence intervals.
- **Canonical provenance:** `tomm_results/A4_CANONICAL_LINEAGE_AUDIT.json` records the checkpoint bundle hash, per-seed checkpoint hashes, archived runtime, calibration-validation hashes, and holdout result hash.
- **A8 submission control:** validated scientific snapshot on `main` at `c3e58a157b0b3bfe58959436e2d02e46d09c40cb`; final TOMM validation run `35455852993` SUCCESS.

## Reviewer-sensitive scope
The RS128 operating point remains traffic-intensive and is reported as a measured deployment constraint. External image-domain evidence consists of BOSSBase development plus Caltech-101 validation through overlapping seeded resamplings. Guo--Ping remains the closest natural-image-selection comparator; its published robustness is kept under its native recovery semantics rather than treated as equivalent to ARCIS exact authenticated whole-message success.

Post-acceptance preservation will create the immutable publication tag/release from the accepted-version lineage; this action does not block the current TOMM submission.
