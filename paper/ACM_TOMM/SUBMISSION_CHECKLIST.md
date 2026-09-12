# ARCIS - ACM TOMM submission checklist

## Manuscript identity
- Title: **ARCIS: Authenticated Robust Coverless Image Signaling with Finite-Index Feasibility**
- Acronym expansion: **Authenticated Robust Coverless Image Signaling**
- Target: **ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)**
- Corresponding author: **Chantal Marguerite Mveh-Abia**
- Author order checked against the latest TOMM manuscript PDF: 7 authors.

## Scientific freeze preserved
- K = 8.
- Group size = 5 covers per coded symbol.
- Reed-Solomon parity = 128 bytes.
- BOSSBase is development evidence; Caltech-101 is external evidence.
- External calibration = 1,800/1,800 authenticated recoveries.
- External holdout = 1,163/1,200 (96.92%).
- Exactly 37 holdout failures, concentrated in 12% central crop.
- Final detector means = 0.5040 (SRM-lite), 0.5128 (GLCM), 0.5266 (CNN).
- DiffStega frozen run = 100/100 cases; correct-recovery PSNR 23.274 dB vs 23.290 dB published.
- No claim of universal undetectability, universal robustness, SOTA superiority, or direct cross-family numerical superiority.

## ACM source-package checks
- ACM `acmart` class used.
- TOMM journal layout uses `acmsmall`.
- Review line numbering enabled.
- Separate BibTeX database supplied.
- All figures are generated in-source with TikZ/PGFPlots; no missing external figure files.
- Every figure includes `\Description{...}` alt text.
- Cover letter source supplied separately.
- No undefined references or citations allowed at delivery.
- The delivered submission ZIP uses one monolithic main `.tex`; the GitHub copy is source-equivalent but split into `ARCIS_TOMM_part*.tex` and included from a wrapper.

## Author re-read before portal submission
1. Re-read title, abstract, introduction, contribution language, limitations, conclusion, and all table values.
2. Confirm all names, accents, affiliations, emails, and author order.
3. Confirm the corresponding-author designation.
4. Confirm data/code availability wording.
5. Confirm conflicts of interest and funding statement in the ScholarOne form.
6. Verify any journal-specific mandatory metadata requested by ScholarOne at the time of submission.

## Repository synchronization
- Public repository URL retained: `https://github.com/EkodeckStephane/NARCIS`.
- README updated to ARCIS/TOMM.
- `SESSION_STATUS.md`, `FINAL_EXPERIMENTAL_REPORT.md`, and `FACT_CHECK.md` updated to the TOMM freeze.
- Historical NARCIS/Elsevier/IEEE manuscript files remain for provenance and are explicitly marked as superseded.
