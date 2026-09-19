# ARCIS — ACM TOMM submission checklist

## Manuscript identity
- Title: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**
- Target: **ACM TOMM**
- Corresponding author: **Chantal Marguerite Mveh-Abia**

## Scientific freeze
- K=8; group size=5; RS128.
- External calibration 1,800/1,800.
- External holdout 1,163/1,200 (96.92%).
- RS0→RS128: 829→1,163 successes; paired endpoint 334 gains / 0 losses, reported descriptively.
- RS128 8/32/64-byte traffic: 2,320 / 2,640 / 3,070 images.
- Detector means across the five seeded Caltech resamplings: 0.5040 / 0.5128 / 0.5266; descriptive ranges 0.5014–0.5052 / 0.5120–0.5138 / 0.5232–0.5301.
- Cross-seed Caltech runs are overlapping train--index resamplings, not independent external replications.
- Direction E′ integrated.
- Canonical A5 component ablation: ARCIS 1,163/1,200; random groups 1,042; uniform scheduler 1,160; fixed mapping 1,166; matched bucket 1,038.
- Guo--Ping 2026 complete primary source audited; its 99.54/98.64/97.19% values are retained under per-representative native semantics and are not conflated with ARCIS authenticated whole-message recovery.

## Editorial checks
- Abstract follows Context → Objective → Methods → Results → Conclusion.
- Main text and Cover Letter use the same seeded-resampling interpretation.
- ScholarOne metadata, title, acronym, author order, abstract, keywords and corresponding-author metadata are synchronized.
- A3 control-plane evidence is synchronized across manuscript, ScholarOne and Cover Letter.
- Independence-based five-run confidence intervals and McNemar significance claims are absent from the current TOMM narrative.

## Submission-control checks
- [x] A4: archived canonical checkpoint bundle verified byte-for-byte; all five checkpoint SHA-256 values match the recorded fresh campaign; canonical holdout aggregate is 1,163/1,200.
- [x] A3: 150/150 metadata roundtrips; all tested tamper, replay, and wrong-receiver cases rejected; evidence integrated in manuscript.
- [x] A5: canonical component ablation reproduced the A4 holdout result exactly and the Guo–Ping 2026 primary-source comparator audit is integrated.
- [x] Final TOMM source validation succeeded on the validated scientific snapshot: run `35460375489` — SUCCESS.
- [x] A8: repair branch merged to `main`.
- [x] A8: submitted scientific state is uniquely identified by commit `254f31e7c44e43f104509c117b0efb4c414dcdcd`.
- [x] A8: **CLOSED for TOMM submission**.

## Post-acceptance preservation — not a submission blocker
- [ ] Create the immutable publication tag/release from the accepted-version lineage.
- [ ] Optionally archive the accepted artifact in a long-term repository/DOI service if desired.

## Gate 10 finalization
- [ ] Automated claim/code/data verifier PASS on the synchronized snapshot.
- [ ] Compiled PDF inspected for clipping, overflow, unreadable figures/tables, and unresolved references.

## Before portal upload
Confirm author names, affiliations, e-mails, CRediT roles, funding, competing interests, AI-use wording if required, and final human reread.
