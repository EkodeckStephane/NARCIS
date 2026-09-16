# ARCIS — Final Q1 Scientific and Editorial Audit

Target: **ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)**

Manuscript: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**

## Final status

**Q1 Gate 10: PASS for the scientific package.**

**Senior Reviewer prescreen:** no critical or major scientific defect remains in the current bounded-claim manuscript. The remaining items are ordinary author-side submission confirmations (affiliations, authorship/CRediT approval, declarations, and portal metadata).

## Gate 1 — Scientific object before artifact description: PASS

The scientific object is finite-index authenticated cover-selection signaling under channel perturbations. The manuscript separates the implemented protocol from the analytical planning model and from contextual comparator evidence. Repository mechanics do not organize the scientific narrative.

## Gate 2 — Claim/evidence alignment: PASS

The headline claims map to direct formal or experimental evidence:

- finite-index feasibility is stated as the realized demand/capacity condition `d_k <= a_k` for every label;
- external calibration reports 1,800/1,800 authenticated recoveries;
- external holdout reports 1,163/1,200 authenticated recoveries;
- the RS ablation is a controlled fixed-upstream sweep over 1,200 holdout trials per parity level;
- communication cost is reported in actual transmitted image counts for the implemented five-cover majority construction;
- the blocking-risk probabilities are explicitly conditional on an i.i.d.-uniform multinomial demand idealization;
- detectability claims are detector-scoped and do not assert universal steganographic secrecy.

Negative evidence remains visible: 37 RS128 holdout failures occur under the 12% central crop, carrier volume is high, and the measured CNN AUC is above chance.

## Gate 3 — Final scientific narrative: PASS

The manuscript presents the final protocol and evidence rather than the history of debugging or repair. Exact hashes, frozen execution details, and machine-readable audit evidence are delegated to the repository/artifact package.

## Gate 4 — Novelty and related work: PASS WITH BOUNDED WORDING

The protected contribution is not any individual standard primitive. The paper's object is the integrated finite-index construction combining calibration-locked symbolization, complementary majority group banks, exact session balancing, authenticated recovery, finite-index feasibility, and detector-scoped evaluation. AES-GCM, Reed-Solomon coding, Gray coding, VICReg-style representation learning, and standard detector/classifier families are identified as adopted components rather than claimed inventions.

The manuscript avoids unsupported priority claims and keeps cross-family comparisons descriptive where communication semantics differ.

## Gate 5 — Experimental validity: PASS FOR REPORTED CLAIMS

The development/external boundary is explicit: BOSSBase supports operating-point development and Caltech-101 supplies five frozen external partitions. Descriptor-training images and indexed covers are image-disjoint within each partition. Calibration transformations determine design choices; holdout transformations remain reserved for validation.

The RS parity ablation changes the parity budget while retaining the upstream learned representation, projection-selection rule, and group-bank construction. Its aggregate results are:

| RS parity bytes | Authenticated recoveries | Success rate | Mean transmitted images/session |
|---:|---:|---:|---:|
| 0 | 829/1200 | 69.08% | 970.0 |
| 32 | 1064/1200 | 88.67% | 1396.7 |
| 64 | 1115/1200 | 92.92% | 1825.0 |
| 96 | 1145/1200 | 95.42% | 2250.0 |
| 128 | 1163/1200 | 96.92% | 2676.7 |

This directly supports a reliability/communication tradeoff claim rather than an unqualified robustness claim.

Repeated detector splits are treated as descriptive repeated-split evidence rather than independent confirmatory samples.

## Gate 6 — Article structure and prose: PASS

The abstract follows problem → gap → method → principal evidence → bounded conclusion. Methods, results, discussion, limitations, and reproducibility roles are separated. DiffStega is contextual executable positioning rather than a headline numerical ranking against a different communication object.

## Gate 7 — Scope and operational claims: PASS

The manuscript does not claim universal undetectability, traffic-analysis resistance, production deployment, or universal channel robustness. Cryptographic payload confidentiality/authenticity is separated from selection detectability. The finite-index blocking probabilities are labeled as a conditional planning model, not as measured operational security.

## Gate 8 — Reproducibility: PASS

The historical TOMM implementation lineage is frozen at commit:

`b8ee42d547b580b9e1639de559b1dfa6ea88d4ef`

It contains the exact group-bank construction, signature-balanced scheduler, cyclic keyed mapping, external-validation runner, detector workflows, and tests used by the evidence lineage. Machine-readable repair evidence is stored under `tomm_results/`.

## Gate 9 — Bibliographic/editorial hygiene: PASS SUBJECT TO FINAL AUTHOR CONFIRMATIONS

Critical recent positioning references and the main TOMM-relevant multimedia/steganalysis references were rechecked during closure. Terminology and principal numerical claims have been synchronized around ARCIS. Before portal upload, authors should still confirm final affiliations, CRediT allocation, corresponding-author metadata, competing-interest text, and any publisher-specific declaration fields.

## Gate 10 — Submission readiness: PASS

For the claims now present, no unresolved contribution/evidence mismatch, conceptual-versus-implemented ambiguity, unjustified causal/operational claim, headline baseline mismatch, or known article/code/data contradiction remains.

The current bounded manuscript is scientifically closed for submission preparation.

## Senior Reviewer prescreen

### Principal strengths supported by evidence

1. The evaluation unit is authenticated plaintext recovery, not only average symbol accuracy.
2. Finite-index feasibility is made explicit at complete-session level.
3. The RS ablation isolates an important reliability/cost mechanism and exposes its carrier-volume price.
4. Selection detectability is evaluated independently from cryptographic protection.
5. External validation uses five deterministic Caltech-101 partitions with reserved holdout transformations.
6. Comparator semantics are separated instead of converting heterogeneous metrics into an artificial ranking.

### Remaining limitations — bounded, not submission blockers

1. The present five-cover construction is carrier intensive: 2,320–3,070 transmitted images for 8–64 byte plaintexts at RS128.
2. The external corpus is Caltech-101; broader native-resolution corpora would strengthen generalization.
3. Detector-scoped near-chance/small-AUC behavior is not a proof of steganographic undetectability.
4. The finite-index blocking-risk probabilities rely on an explicitly stated multinomial planning idealization.
5. Traffic-level sequence analysis remains outside the evaluated security claim.

### Prescreen decision

**Minor-revision / acceptability range under the present bounded claims.** No new experiment is required to support the claims currently retained in the manuscript. Remaining actions are consistency and submission-package checks rather than scientific reconstruction.
