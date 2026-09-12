# ARCIS — ACM TOMM submission snapshot

This directory is the canonical manuscript snapshot for:

**ARCIS: Authenticated Robust Coverless Image Signaling with Finite-Index Feasibility**

Target: **ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)**.

## Files

- `ARCIS_TOMM.tex` — wrapper for the current ACM manuscript source split into `ARCIS_TOMM_part*.tex` for repository transport.
- `ARCIS_references.bib` — BibTeX database.
- `COVER_LETTER_ARCIS_TOMM.tex` — cover letter source.
- `SUBMISSION_CHECKLIST.md` — portal and consistency checks.
- `SCHOLARONE_METADATA.txt` — title, abstract, author order, keywords, and corresponding-author metadata.
- `REVISION_MANIFEST.md` — frozen operating point, headline results, and artifact hashes.

The locally delivered submission ZIP keeps the manuscript as one monolithic `ARCIS_TOMM.tex`; the GitHub snapshot is content-equivalent but split with `\input{...}` so the repository connector can preserve the full source reliably.

## Build

```text
pdflatex ARCIS_TOMM.tex
bibtex ARCIS_TOMM
pdflatex ARCIS_TOMM.tex
pdflatex ARCIS_TOMM.tex
```

The manuscript uses the ACM `acmart` class in `acmsmall` review mode. TikZ/PGFPlots figures are generated directly from source.

## Naming

ARCIS is the current protocol/article name. The repository name `NARCIS` and Python package namespace `narcis` are retained for backward-compatible reproducibility. See the root `PROJECT_RENAME.md`.
