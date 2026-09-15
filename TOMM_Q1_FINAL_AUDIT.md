# NARCIS — Q1 Scientific-Article Gates and Senior Reviewer Final Prescreen

**Journal:** ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)  
**Manuscript:** *NARCIS: Authenticated Neural Coverless Image Signaling with Attack-Qualified Codebooks and Error Correction*  
**Authors:** Arthur Ulrich Ewane; Juvet Karnel Sadié; Stéphane Gaël R. Ekodeck; Serge Alain Ebélé; Vivien Loïck Beyala Kamgang; Damaris Belle M. Fotso; Chantal Marguerite Mveh-Abia (corresponding author).

## Gate 1 — Scientific object before artifact description: PASS
The paper is organized around finite-index authenticated coverless signaling under channel and selection-detectability constraints. Repository mechanics remain confined to reproducibility.

## Gate 2 — Claim/evidence alignment: PASS
Every headline number maps to canonical JSON/CSV evidence. Standard AES-GCM, Reed–Solomon, HMAC, Gray coding, and CNN components are presented through their protocol roles. The scientific contribution is the integrated finite-index construction and its externally frozen validation. The 12% crop boundary and CNN selection signal remain visible in the main results.

## Gate 3 — Final scientific narrative: PASS
The manuscript follows a self-contained scientific narrative. BOSSBase is explicitly labeled development evidence and Caltech-101 supplies external validation. The final text avoids rejection history, phase/RQ notation, debugging narrative, and unnecessary negative/corrective phrasing.

## Gate 4 — Novelty and current related work: PASS WITH BOUNDED WORDING
The protected contribution couples calibration-locked codebook choice, complementary majority group banks, failure-signature-balanced keyed scheduling, exact K-cycle symbol-to-cluster balancing, authenticated framing, and explicit finite-message feasibility. Current TOMM and close coverless/steganalysis literature is integrated by scientific role, including recent work on generative steganography, robust coverless communication, image steganalysis, adversarial embedding, and multimedia authentication.

## Gate 5 — Experimental validity and statistics: PASS FOR REPORTED CLAIMS
The final operating point is frozen before Caltech outcomes. Five deterministic external partitions are used; representation-training and cover-index images are disjoint. Calibration and holdout transformations are disjoint. Final detector evaluation uses 100 image-disjoint repeated splits per detector. Repeated-split intervals are interpreted descriptively because the splits overlap. DiffStega is executed from a frozen official commit and evaluated in its native reconstruction domain.

The enriched manuscript exposes development-to-external transfer: BOSSBase K=8 development results, complete-index usage, external calibration, holdout generalization, partition variability, detector variability, and DiffStega reproduction appear as separate evidence layers.

## Gate 6 — Article structure, prose, figures, tables: PASS
The abstract follows problem → gap → method → evidence → bounded conclusion. The article contains **nine figures and nine tables**: protocol pipeline, exact cyclic mapping, BOSSBase development diagnostics, calibration/index-use diagnostics, holdout robustness by attack, holdout robustness by partition, detector comparison, CNN partition variability, DiffStega reproduction, plus corresponding evidence tables. Scientific figures are TikZ/PGFPlots-native and include ACM accessibility descriptions where required. The final compiled review manuscript has **18 pages**; the strengthened ACM CI build passes compilation, reference resolution, and overflow checks.

## Gate 7 — Scope and operational claims: PASS
The supported security wording is **low but measurable selection leakage** under the evaluated warden. Robustness is strong and bounded to the declared channel, with the 12% crop result defining the strongest observed boundary. Production key management, broader traffic analysis, and additional external image domains are separated as future deployment/research extensions.

## Gate 8 — Reproducibility without report dominance: PASS WITH DISCLOSED METRIC-ENVIRONMENT EXCEPTION
The repository contains protocol freezes, dataset/checkpoint provenance, canonical machine-readable results, detector schedules/raw rows, commands, hashes, and workflow evidence. DiffStega benchmark execution is frozen; its independent metric environment contains two disclosed post-processing package-version deviations.

## Gate 9 — Bibliographic/editorial hygiene: PASS
Critical recent references were checked against primary/publisher records. The JoCS bibliographic record is corrected to Chang Ren and Bin Wu, *Cybersecurity* 7, article 73 (2024), DOI `10.1186/s42400-024-00299-5`. Title and seven-author order are synchronized across manuscript/status/cover-letter assets.

## Gate 10 — Submission readiness: PASS
Final GitHub Actions run **35021173166** (run 121), manuscript head commit `4b4cf7f888904719fc2187178ad3ddbe256df023`, passed both the scientific/code job and the strengthened ACM manuscript job. The 18-page manuscript and 1-page cover letter compile successfully; unresolved-reference/citation and `Overfull \\hbox` guards pass; both submission PDFs are exported in artifact `NARCIS-TOMM-submission-pdfs` (ID **10417935612**, digest `sha256:c1e25e34ce949d6159d06bd4c3fdf47292b6e7062266ff07b62128ef96711612`).

## Senior Reviewer Q1/Rang A prescreen

### Calibration
- Primary domain: multimedia security / coverless image steganography and steganalysis.
- Secondary domains: robust representation learning, coding, authenticated communication.
- Contribution type: protocol/algorithmic construction plus development evidence, external experimental validation, detector audit, and external baseline reproduction.
- Maturity claimed: laboratory implementation and external-corpus validation.

### Promise–evidence assessment
The central promise—reliable finite-index authenticated signaling with explicitly measured selection leakage—is supported under the declared protocol. The enriched manuscript gives a dense evidence chain: development transfer, cover-index usage, attack-specific channel results, partition-level variation, detector-level variation, and reproduction diagnostics are all visible in the paper.

### Reviewer-visible boundaries
1. Caltech-101 supplies the current untouched external image-domain validation; broader corpora are a natural extension.
2. The 12% crop condition defines the principal observed robustness boundary.
3. CNN AUC 0.527 establishes weak but reproducible selection leakage.
4. DiffStega is an executable recent reference with different communication semantics.
5. A future component-removal study can isolate causal contribution sizes beyond the exact construction properties already established.

### Editorial recommendation from the prescreen
**Minor Revision / publishable evidence level.** The completed study contains the central evidence required for the claims as written; likely reviewer requests concern exposition or broader future validation rather than a missing central experiment.

## Final decision

**GATE-10 PASS.**

The TOMM submission package is scientifically claim-safe and mechanically validated under the stated scope. This prescreen assesses submission readiness rather than predicting the journal's editorial decision.