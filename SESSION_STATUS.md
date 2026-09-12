# ARCIS Session Status

## Current status

- Current method/article name: **ARCIS — Authenticated Robust Coverless Image Signaling**.
- Current title: **ARCIS: Authenticated Robust Coverless Image Signaling with Finite-Index Feasibility**.
- Target journal: **ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)**.
- Submission status: **not yet submitted**; the submission package is frozen for a final author reread.
- Canonical manuscript directory: `paper/ACM_TOMM/`.

The repository itself keeps the historical name `NARCIS`, and the Python namespace remains `src/narcis/`, to preserve reproducibility and stable paths.

## Frozen protocol

- `K = 8`.
- Group size = 5 covers per coded symbol.
- Reed–Solomon parity = 128 bytes.
- BOSSBase 1.01 = development evidence.
- Caltech-101 = external frozen evaluation.
- Five deterministic seeds: 11, 29, 47, 71, 101.

## Frozen headline evidence

- BOSSBase development calibration: 1,800/1,800 authenticated recoveries.
- BOSSBase index participation: 7,995–8,000 unique covers per seed.
- Caltech-101 external calibration: 1,800/1,800 authenticated recoveries.
- Caltech-101 unseen holdouts: 1,163/1,200 (96.92%).
- The 37 holdout failures are all in the unseen 12% central-crop condition; the other seven holdouts achieve 150/150 each.
- Final image-disjoint detector means: 0.5040 (SRM-lite/ExtraTrees), 0.5128 (GLCM/logistic regression), 0.5266 (30-head CNN).
- Frozen DiffStega execution: 100/100 UniStega cases completed; correct-recovery PSNR 23.274 dB reproduced versus 23.290 dB published.

## Canonical submission assets

- `paper/ACM_TOMM/ARCIS_TOMM.tex`
- `paper/ACM_TOMM/ARCIS_references.bib`
- `paper/ACM_TOMM/COVER_LETTER_ARCIS_TOMM.tex`
- `paper/ACM_TOMM/SUBMISSION_CHECKLIST.md`
- `paper/ACM_TOMM/SCHOLARONE_METADATA.txt`
- `paper/ACM_TOMM/REVISION_MANIFEST.md`

Older Signal Processing and IEEE/TMM assets are retained only as historical revisions.

## Next action

Perform the final human reread of the ACM TOMM PDF. Any post-reread correction should update the `.tex`, compiled PDF, portal metadata/checklist where affected, and this repository snapshot together before submission.
