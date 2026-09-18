# ARCIS / ACM TOMM revision manifest

## Identity

- Title: **ARCIS: Authenticated Robust Cover-Selection Image Signaling with Finite-Index Feasibility**
- Acronym: **ARCIS = Authenticated Robust Cover-Selection Image Signaling**
- Target: **ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)**
- Corresponding author: **Chantal Marguerite Mveh-Abia**
- Status: submission-ready snapshot pending final author reread.

## Frozen operating point

- `K = 8`
- group size = 5 covers per coded symbol
- Reed–Solomon parity = 128 bytes
- BOSSBase 1.01 = development evidence
- Caltech-101 = external evaluation
- seeds = 11, 29, 47, 71, 101

## Frozen headline results

- BOSSBase development calibration: 1,800/1,800 authenticated recoveries.
- Caltech external calibration: 1,800/1,800 authenticated recoveries.
- Caltech holdout: 1,163/1,200 (96.92%).
- Holdout failures: 37, all in the 12% crop; 12% crop = 113/150.
- Other seven holdout transformations: 150/150 each.
- Final mean macro-AUC: SRM-lite 0.5040; GLCM 0.5128; CNN 0.5266.
- DiffStega: 100/100 UniStega cases completed; correct-recovery PSNR 23.274 dB vs 23.290 dB published.

## Delivered artifact hashes (SHA-256)

These hashes identify the local submission artifacts delivered for the final author reread:

- `ARCIS_TOMM.tex`: `5a352d216b526b88fb565d7d298e32f124c6ddd51d682efdb1b79b499be5cd62`
- `ARCIS_references.bib`: `e7e4f52428a0ea5b27e1a5581517f3aec7e9f6856eff6768872b4f842a467ad1`
- `ARCIS_TOMM.pdf`: `61995c4fc92798599b7b272f802fe989c908f2f82faa652378b8489f94b19545`
- `COVER_LETTER_ARCIS_TOMM.pdf`: `b145de8a5a7d48070542da214f3da42920a94d90ba360a8211f5776880053392`

The GitHub copy of the manuscript source is split into `ARCIS_TOMM_part*.tex` and included from `ARCIS_TOMM.tex`; this is content-equivalent at the LaTeX level but therefore has a different file-level hash from the delivered monolithic `.tex`.

## Comparator freeze

DiffStega upstream commit used by the manuscript:

`73cd7cb8d102f4fc0f5bb168a71cfb948077d89a`

The manuscript records the evidence-bundle SHA-256:

`32d0e975eb197adb0d1d2f7c537b04b4fab84af45a51148eaf15872b40de1f46`

## Repository continuity

The repository retains the historical name `EkodeckStephane/NARCIS` and implementation namespace `src/narcis/` to preserve reproducibility. ARCIS is the current protocol/article name.


## Final scientific closure
RS-parity ablation, communication cost, conditional blocking-risk analysis, and the demotion of DiffStega from headline comparison are incorporated in the current ARCIS/TOMM freeze.
