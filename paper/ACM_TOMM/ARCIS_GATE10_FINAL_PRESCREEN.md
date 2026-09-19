# ARCIS — Final Q1 / Senior Reviewer Prescreen

Target: **ACM TOMM**  
Scientific snapshot: `254f31e7c44e43f104509c117b0efb4c414dcdcd`  
Main validation: `35460375489` — **SUCCESS**

## Gate-by-gate status

| Gate | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Scientific object is clear and falsifiable | PASS | finite-index authenticated signaling object, explicit success criterion, bounded threat/channel model |
| 2 | Every major claim has direct evidence | PASS | `CLAIM_EVIDENCE_MATRIX.md`, A3/A4/A5 audits, detector/parity/traffic/finite-index artifacts |
| 3 | Final article contains no debugging narrative | PASS | manuscript-facing provenance is limited to canonical evidence; noncanonical diagnostics remain outside the article |
| 4 | Novelty is positioned against direct SOTA | PASS | Guo--Ping 2026 primary-source audit, positioning table, finite-index/authenticated-whole-message distinction |
| 5 | Baselines, units, uncertainty and confounds are handled | PASS | canonical matched A5 ablation; native comparator semantics; dependence-aware descriptive reporting |
| 6 | Structure and figures are submission-quality | PASS | 20-page CI PDF compiled without overfull boxes or unresolved references; 200-dpi rendered inspection found no clipping, overlap, broken glyphs, or out-of-margin tables |
| 7 | Guarantees are bounded to the evaluated snapshot | PASS | limitations/threats section, held-out parameterization wording, detector and comparator scope |
| 8 | Reproducibility package separates manuscript from evidence | PASS | hashes, manifests, machine-readable results, verifier scripts, stable scientific commit |
| 9 | References, numbers, title, abstract, tables and conclusion are coherent | PASS | synchronized title/metadata; BibTeX build; Guo--Ping source audit; canonical numeric checks; final static verifier PASS |
| 10 | Zero claim/evidence/code/data/review mismatch | PASS | Gate 10 static verifier PASS and rendered-PDF inspection PASS on workflow run `35465970002` |

## Current reviewer-sensitive findings

1. The strongest deployment limitation is carrier volume: 2,320--3,070 images at RS128 for 8--64 byte plaintexts.
2. Fixed mapping reaches 1,166/1,200 versus ARCIS 1,163/1,200; therefore the cyclic map is justified by balance, not recovery.
3. Guo--Ping 2026 reports 99.54/98.64/97.19% under a per-representative metric; these values must never be presented as directly equivalent to ARCIS authenticated whole-message recovery.
4. Caltech seeds are overlapping resamplings of one corpus; no independence-based five-run inference is permitted.
5. The post-acceptance GitHub tag/release is preservation, not a submission gate.

**Final prescreen verdict: PASS.** The automated claim/code/data verifier and the rendered-PDF inspection both pass. The article is submission-ready subject only to the normal human portal-entry check.
