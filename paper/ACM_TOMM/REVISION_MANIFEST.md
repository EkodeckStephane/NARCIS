# ARCIS / ACM TOMM revision manifest

## Identity
- Title: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**
- Acronym: **ARCIS = Authenticated Robust Cover-Selection Image Signaling**
- Target: **ACM TOMM**
- Corresponding author: **Chantal Marguerite Mveh-Abia**
- Repair provenance branch: `arcis-a1-a10-repair`
- Validated scientific submission snapshot: `main` commit `c3e58a157b0b3bfe58959436e2d02e46d09c40cb`
- Final TOMM validation: run `35455852993` — **SUCCESS**

## Frozen operating point
- K = 8
- group size = 5
- RS parity = 128 bytes
- development corpus = BOSSBase 1.01
- external corpus = Caltech-101
- external seeds = 11, 29, 47, 71, 101
- per seed = 1,500 descriptor-training images + 7,000 cover-index images, disjoint within run
- cross-seed interpretation = overlapping train--index resamplings of the same 9,144-image corpus, not independent external replications

## Scientific and editorial closure
- dependence-aware detector and parity reporting integrated;
- session-volume side-channel analysis integrated;
- finite-index necessity/sufficiency proof integrated;
- ScholarOne metadata and Cover Letter synchronized;
- **A3 CLOSED:** 150/150 control-plane metadata roundtrips; all 5 tested tamper, replay, and wrong-receiver cases rejected;
- **A4 CLOSED:** byte-identical canonical checkpoint bundle verified, all five recorded checkpoint SHA-256 values matched, canonical holdout aggregate verified at 1,163/1,200;
- **A5 CLOSED:** canonical component ablation reproduces ARCIS 1,163/1,200 and records random-groups 1,042/1,200, uniform-scheduler 1,160/1,200, fixed-mapping 1,166/1,200, and matched-bucket 1,038/1,200; Guo–Ping 2026 comparator audited from the complete primary source;
- canonical A3/A4 audit files stored in `tomm_results/`;
- noncanonical retraining workflows removed from the submission lineage;
- **A8 CLOSED for TOMM submission:** final validation succeeded and the repair branch was merged to `main`.

## A4 provenance
- recorded fresh campaign commit: `bdef888c90d191550a1e3ae29ec25b4a2d422e66`;
- checkpoint bundle SHA-256: `8193bb8462d5b79fb18462e8e55091b8982752161ed388e95b7b7785483ed1f1`;
- canonical holdout aggregate SHA-256: `27f99fa00e9e8a7f1792195799615e8c8235718fa613fc20476a9f6014c70fcf`;
- archived runtime: Python 3.13.5, PyTorch 2.10.0+cpu, NumPy 2.3.5, pandas 2.2.3, scikit-learn 1.8.0, SciPy 1.17.0, Pillow 12.3.0, cryptography 46.0.4.

## Submission-control closure
A8 for the current TOMM submission requires:
1. final TOMM source validation at the scientific submission snapshot — **DONE / SUCCESS**;
2. merge of the repaired scientific state to `main` — **DONE**;
3. stable identification of the submitted scientific snapshot by commit SHA — **DONE**.

A GitHub tag/release is **not required to close A8 for submission**. The publication lineage will be frozen by tag/release after acceptance, when the accepted-version source is known.

Global Gate 10 remains separate from A3/A4/A5/A8 and must not be inferred from these closures if another A1–A10 item remains partial.
