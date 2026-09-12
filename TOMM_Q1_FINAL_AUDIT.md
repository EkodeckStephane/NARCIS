# NARCIS — Q1 Scientific-Article Gates and Senior Reviewer Final Prescreen

**Journal:** ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)  
**Manuscript:** *NARCIS: Authenticated Neural Coverless Image Signaling with Attack-Qualified Codebooks and Error Correction*

## Gate 1 — Scientific object before artifact description: PASS
The paper is organized around finite-index authenticated coverless signaling under channel and selection-detectability constraints. Repository mechanics are confined to reproducibility.

## Gate 2 — Claim/evidence alignment: PASS
Every headline number in the abstract maps to canonical JSON/CSV evidence. AES-GCM, Reed–Solomon, HMAC, Gray coding, and CNNs are not presented as novel primitives. The 12% crop failures and CNN selection signal are reported rather than hidden by wording.

## Gate 3 — Final scientific narrative: PASS
The manuscript contains no rejection history, correction chronology, phase/RQ labels, TODO markers, or debugging narrative. BOSSBase appears only because its development role is methodologically required to interpret Caltech-101 as external validation.

## Gate 4 — Novelty and current related work: PASS WITH BOUNDED WORDING
The protected contribution is the finite-index construction coupling calibration-locked codebook choice, complementary majority group banks, failure-signature-balanced keyed scheduling, exact K-cycle symbol-to-cluster balancing, authenticated framing, and explicit message feasibility. The manuscript disclaims novelty of standard components and avoids unsupported “first” or “state-of-the-art” priority language. Current TOMM and close coverless/steganalysis literature is integrated by scientific role.

## Gate 5 — Experimental validity and statistics: PASS FOR REPORTED CLAIMS
The final operating point was frozen before Caltech outcomes. Five deterministic external partitions are used; representation training and index images are disjoint. Calibration and holdout attacks are disjoint. Final detector evaluation uses 100 image-disjoint repeated splits per detector. Overlapping repeated splits are not treated as independent confirmatory observations; intervals are labeled descriptive. DiffStega is executed from a frozen official commit and kept semantically separate from NARCIS. No unmatched superiority claim is made.

The paper does not claim a component-level causal performance gain from empirical removal ablations. Component roles are supported by exact construction properties or integrated-protocol evidence, and this boundary is stated explicitly.

## Gate 6 — Article structure, prose, figures, tables: PASS
The abstract follows problem → gap → method → external evidence → bounded conclusion. The paper contains a protocol figure, recent-work positioning table, component/evidence table, calibration table, unseen-holdout table, detector table/plot, DiffStega reproduction table, discussion, validity threats, reproducibility, and conclusion. The final ACM review build is 13 pages and has no unresolved citation/reference or overfull-box warning.

## Gate 7 — Scope and operational claims: PASS
No universal robustness, universal steganographic secrecy, Internet traffic-analysis security, production KMS, or deployment-readiness claim is made. NARCIS is explicitly low but measurably detectable under the strongest evaluated CNN warden. The crop-12 boundary is explicit.

## Gate 8 — Reproducibility without report dominance: PASS WITH DISCLOSED METRIC-ENVIRONMENT EXCEPTION
The repository contains protocol freezes, dataset/checkpoint provenance, canonical machine-readable results, detector schedules/raw rows, commands, hashes, and workflow evidence. DiffStega benchmark execution is frozen; its independent metric environment differs in two post-processing package versions, disclosed in the manuscript and audit.

## Gate 9 — Bibliographic/editorial hygiene: PASS
All final citation keys resolve in the local build. Critical recent references were checked against primary/publisher records. The JoCS record was corrected to Chang Ren and Bin Wu, *Cybersecurity* 7, article 73 (2024), DOI `10.1186/s42400-024-00299-5`. The title and author order are synchronized across final assets.

## Gate 10 — Submission readiness: PASS FOR THE STATED STUDY
No unresolved scientific contradiction remains between the final manuscript and frozen evidence. No essential new experiment is required for a claim currently made. Residual limitations are genuine boundaries of the stated study and are disclosed.

## Senior Reviewer Q1/Rang A prescreen

### Calibration
- Primary domain: multimedia security / coverless image steganography and steganalysis.
- Secondary domains: robust representation learning, coding, authenticated communication.
- Contribution type: protocol/algorithmic construction plus external experimental validation and reproducibility study.
- Maturity claimed: laboratory implementation and external-corpus validation; no production deployment.

### Promise–evidence assessment
The central promise—reliable finite-index authenticated signaling with explicitly measured selection leakage—is supported under the declared protocol. The manuscript does not transform unchanged pixels into an undetectability claim. The strongest adverse results are visible in the abstract, results, and limitations.

### Remaining reviewer concerns (non-blocking)
1. One untouched external corpus does not establish universal image-domain transfer.
2. The 12% crop condition remains a material failure boundary.
3. CNN AUC 0.527 establishes a weak but reproducible selection signal.
4. DiffStega provides an executable external reference but not a matched-protocol capacity baseline.
5. A component-removal study could answer a future causal-design question, but the present manuscript does not make a component-level superiority claim that requires it.

### Editorial recommendation from the prescreen
**Minor Revision / publishable evidence level.** No new central experiment or proof is required for the claims as written; likely reviewer requests would concern exposition, additional comparison discussion, or broader future validation. This prescreen is not a prediction of TOMM's editorial decision.

## Final decision

**GATE-10 PASS.** The TOMM submission package is scientifically claim-safe under the stated scope.
