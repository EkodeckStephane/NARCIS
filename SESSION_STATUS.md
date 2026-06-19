# NARCIS Session Status

## Status

- Submission status: submitted.
- Target journal: Signal Processing (Elsevier/EURASIP).
- Article type: Original Research Article.
- Current action: wait for editorial and reviewer feedback.
- Session recorded: 10 June 2026, Africa/Douala.

## Submitted work

Title:

> NARCIS: Authenticated Neural Coverless Image Signaling with
> Attack-Qualified Codebooks and Error Correction

The manuscript positions NARCIS as an end-to-end coverless communication
protocol based on unchanged natural images, attack-qualified codebooks,
AES-GCM protection, Reed--Solomon correction, keyed symbol assignment, and
authenticated recovery.

## Main reported evidence

- BOSSBase and Caltech-101 evaluations with five deterministic partitions per
  dataset.
- 1,575/1,575 authenticated message-condition recoveries.
- Mean symbol accuracy: 98.74% on BOSSBase and 98.59% on Caltech-101.
- Net plaintext rate: 0.184 to 1.213 bits/cover for the tested payload sizes.
- Matched BOSSBase ablation: 100% success with attack qualification versus
  67.62% without it.
- Selection leakage is reported by dataset and detector, including the weak
  Caltech-101 seed-47 signal.

## Submission assets

- `paper/NARCIS.tex` and `paper/NARCIS.pdf`
- `paper/NARCIS_LaTeX_Source.zip`
- `paper/NARCIS_Highlights.docx`
- `paper/NARCIS_Highlights.txt`
- `paper/Graphical_Abstract.tex`
- `paper/Graphical_Abstract.pdf`
- `paper/Graphical_Abstract.png`
- `paper/cover_letter.tex` and `paper/cover_letter.pdf`
- Figures `paper/figures/Fig_01.pdf` through `Fig_09.pdf`

## Validation state

- Manuscript compiled to 13 pages.
- No undefined figure references or citations were detected.
- All nine manuscript figures are labelled and cited.
- Graphical abstract is implemented in editable TikZ and exported as vector
  PDF and 300 dpi PNG.
- Five highlights satisfy the Elsevier 85-character limit.
- Test suite result: 23 tests passed.
- The standalone LaTeX archive was extracted and compiled successfully.

## Resume point

When the editorial decision arrives:

1. Preserve the complete decision letter and reviewer comments verbatim.
2. Classify every request as scientific, experimental, editorial, or formal.
3. Build a point-by-point response matrix with manuscript locations and
   supporting evidence.
4. Reproduce or extend experiments only where the reviewer request affects a
   claim or acceptance risk.
5. Update the manuscript, response letter, fact check, figures, source archive,
   and GitHub repository together.

Do not infer acceptance from the current submission status. The next phase
starts only from the actual editor and reviewer reports.
