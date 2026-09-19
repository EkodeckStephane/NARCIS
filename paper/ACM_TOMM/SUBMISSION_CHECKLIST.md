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
- Guo--Ping and ARCIS recovery percentages are kept in their native semantic domains.

## Editorial checks
- Abstract follows Context → Objective → Methods → Results → Conclusion.
- Main text and Cover Letter use the same seeded-resampling interpretation.
- ScholarOne metadata, title, acronym, author order, abstract, keywords and corresponding-author metadata are synchronized.
- Independence-based five-run confidence intervals and McNemar significance claims are absent from the current TOMM narrative.

## Release-control checks
- [ ] A4: all five regenerated checkpoint SHA-256 values match the recorded fresh campaign and canonical recovery totals agree.
- [ ] A3: authenticated metadata roundtrip, tamper rejection, and replay rejection are explicitly integrated in the manuscript.
- [ ] Final TOMM source validation succeeds at the release-candidate head.
- [ ] A8: release-candidate branch merged to `main`.
- [ ] A8: immutable tag/release created and recorded in the revision manifest.

## Before portal upload
Confirm author names, affiliations, e-mails, CRediT roles, funding, competing interests, AI-use wording if required, and final human reread.
