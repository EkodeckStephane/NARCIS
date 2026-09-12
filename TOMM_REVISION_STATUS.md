# NARCIS — ACM TOMM Final Revision Status

## Target and frozen title

**ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)**  
**NARCIS: Authenticated Neural Coverless Image Signaling with Attack-Qualified Codebooks and Error Correction**

## Status

**FINAL CLOSURE COMPLETE — GATE-10 PASS.**

The TOMM manuscript integrates the canonical K=8/group-size-5/RS128 lineage at high result density: BOSSBase development evidence, Caltech calibration and complete-index usage, external holdouts, repeated SRM/GLCM/CNN steganalysis, and the 100-case DiffStega reproduction. BOSSBase supports development; Caltech-101 carries the external-validation claims.

## Closed experimental gates

- BOSSBase K=8 development: **1,800/1,800** calibration recoveries over five seeds; **7,995–8,000** unique covers exercised per seed.
- External calibration: **1,800/1,800** authenticated recoveries; all **7,000 covers** exercised in every Caltech partition.
- External holdout: **1,163/1,200 = 96.92%**; `crop_12_holdout` contributes the **37 observed failures**, while seven other attacks achieve **150/150** each.
- Final selection detectors: SRM-lite **0.504048**, GLCM **0.512833**, CNN **0.526603** mean macro-AUC over 100 repeated image-disjoint splits.
- CNN partition means: **0.523150, 0.527023, 0.530054, 0.524239, 0.528548** for seeds 11, 29, 47, 71, and 101.
- DiffStega external execution: **100/100** official UniStega cases, **700 PNG outputs**, zero evaluation errors, correct-recovery PSNR **23.274 dB** versus **23.290 dB** published.
- Claim/code/data audit: **PASS**.
- Q1 gates: **1–10 PASS** under the bounded claims in the final manuscript.

## Manuscript content

- **Nine scientific figures**: protocol pipeline, cyclic K=8 session mapping, BOSSBase development diagnostics, Caltech calibration/index-use diagnostics, holdout robustness by attack, holdout robustness by partition, detector comparison, CNN partition variability, and DiffStega reproduction.
- **Nine tables**: SOTA positioning, component roles, BOSSBase development, external calibration, index usage, holdouts, detector statistics, DiffStega reproduction, and consolidated evidence.
- Security wording: **low but measurable selection leakage/detectability**.
- Robustness wording: strong and bounded to the declared channel, with the 12% crop boundary explicit.
- Standard cryptographic/coding components are presented by role; novelty is attached to the integrated finite-index construction.
- DiffStega metrics are labeled **independently reproduced** and remain within their native reconstruction semantics.
- The two disclosed metric-environment version deviations remain visible.
- Prose is predominantly affirmative; negative formulations are retained only where required to state a scientific boundary or prevent an unsupported claim.

## Final author order

1. Arthur Ulrich Ewane
2. Juvet Karnel Sadié
3. Stéphane Gaël R. Ekodeck
4. Serge Alain Ebélé
5. Vivien Loïck Beyala Kamgang
6. Damaris Belle M. Fotso
7. Chantal Marguerite Mveh-Abia — corresponding author

Juvet Karnel Sadié uses the same University of Yaoundé I/LIRIMA/TEAM GRIMCAPE, UMMISCO-IRD, and Sorbonne Université affiliations as Stéphane Gaël R. Ekodeck. No ORCID is assigned to him in the manuscript. Damaris Belle M. Fotso uses her verified University of Yaoundé I/LIRIMA affiliation, institutional email, and ORCID `0009-0001-8736-0644`.

## Mechanical validation

GitHub Actions run **34708394790** (run 116), head commit `304ffe980cccd9f2217488f4836a2525bc8ba97d`, completed with both jobs green:

- unit tests + TOMM preflight: **PASS**;
- ACM manuscript build: **PASS**;
- cover-letter build: **PASS**;
- unresolved references/citations guard: **PASS**;
- `Overfull \\hbox` guard: **PASS**;
- submission-PDF artifact export: **PASS**.

Artifact `NARCIS-TOMM-submission-pdfs`: ID **10301903911**, size **600,494 bytes**, digest `sha256:327ab7d665c5d55e39c2d310d3aa3dcfbd3f5096d181cf15efc9b7b658368a81`.
