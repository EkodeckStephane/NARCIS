# NARCIS — Final TOMM Closure Record

## Closure decision

The experimental, scientific, editorial, and mechanical closure required for the current manuscript claims is complete.

## Canonical protocol

- K=8 balanced one-dimensional quantile codebook.
- Five covers per coded symbol; strict majority decoding.
- Reed–Solomon parity: 128 bytes.
- 30 authenticated sessions per external partition: 10 each at 8/32/64 plaintext bytes.
- External seeds: 11, 29, 47, 71, 101.
- Balanced cyclic keyed Gray mapping.
- Calibration-failure-signature-balanced group scheduler.
- AES-GCM authenticated payload/session path with sequence-bound associated data and explicit benchmark nonce uniqueness.

## Final author order

1. Arthur Ulrich Ewane
2. Juvet Karnel Sadié
3. Stéphane Gaël R. Ekodeck
4. Serge Alain Ebélé
5. Vivien Loïck Beyala Kamgang
6. Damaris Belle M. Fotso
7. Chantal Marguerite Mveh-Abia — corresponding author

Juvet Karnel Sadié carries the same three affiliations as Stéphane Gaël R. Ekodeck and has no ORCID entry. Damaris Belle M. Fotso carries her verified University of Yaoundé I/LIRIMA affiliation, institutional email, and ORCID `0009-0001-8736-0644`.

## Frozen evidence

- BOSSBase development: **1,800/1,800** calibration recoveries across five seeds; **7,995–8,000** unique covers exercised per seed.
- Caltech calibration: **1,800/1,800** authenticated recoveries and **7,000/7,000** covers exercised in every partition.
- Holdout: **1,163/1,200 (96.92%)**; seven attacks achieve **150/150**, while crop 12% yields **113/150**.
- Detectability: SRM-lite **0.5040**; GLCM **0.5128**; CNN **0.5266** mean macro-AUC.
- CNN partition means: **0.5232–0.5301**.
- DiffStega: **100/100** official cases completed; **700 PNGs**; correct-recovery PSNR **23.274 dB** vs. **23.290 dB** published; evidence SHA-256 `32d0e975eb197adb0d1d2f7c537b04b4fab84af45a51148eaf15872b40de1f46`.

## Final manuscript content controls

- ACM `acmart` review-manuscript format.
- **18-page** compiled manuscript and **1-page** cover letter.
- **Nine scientific figures** using TikZ/PGFPlots, covering the protocol pipeline, cyclic session mapping, BOSSBase development diagnostics, calibration/index-use diagnostics, holdout robustness by attack and partition, detector comparison, CNN partition variability, and DiffStega reproduction.
- **Nine tables** covering positioning, component roles, development results, external calibration, index usage, holdouts, detector statistics, DiffStega reproduction, and consolidated evidence.
- Positive/affirmative scientific phrasing used throughout, with boundary statements retained where scientifically necessary.
- BOSSBase explicitly labeled as development evidence; Caltech-101 carries external claims.
- Historical K=16/1,575-trial values excluded from final claims.
- Crop 12% and CNN leakage retained as explicit scientific boundaries.

## Mechanical validation

Final GitHub Actions run **35021173166** (run 121), manuscript head commit `4b4cf7f888904719fc2187178ad3ddbe256df023`, completed successfully on September 15, 2026:

- unit tests: **PASS**;
- TOMM preflight: **PASS**;
- ACM manuscript compilation: **PASS**;
- cover-letter compilation: **PASS**;
- unresolved citation/reference guard: **PASS**;
- `Overfull \\hbox` guard: **PASS**;
- submission-PDF artifact upload: **PASS**.

Artifact `NARCIS-TOMM-submission-pdfs`: ID **10417935612**, size **600,493 bytes**, digest `sha256:c1e25e34ce949d6159d06bd4c3fdf47292b6e7062266ff07b62128ef96711612`.

## Gate decision

**Q1 Gate 10: PASS.**

The manuscript is claim-safe, evidence-rich, editorially synchronized, and mechanically validated for TOMM submission under its stated scope. This closure certifies submission readiness rather than editorial acceptance.