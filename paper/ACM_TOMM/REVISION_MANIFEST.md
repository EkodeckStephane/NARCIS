# ARCIS / ACM TOMM revision manifest

## Identity
- Title: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**
- Acronym: **ARCIS = Authenticated Robust Cover-Selection Image Signaling**
- Target: **ACM TOMM**
- Corresponding author: **Chantal Marguerite Mveh-Abia**
- Current release-candidate branch: `arcis-a1-a10-repair`

## Frozen operating point
- K = 8
- group size = 5
- RS parity = 128 bytes
- development corpus = BOSSBase 1.01
- external corpus = Caltech-101
- external seeds = 11, 29, 47, 71, 101
- per seed = 1,500 descriptor-training images + 7,000 cover-index images, disjoint within run
- cross-seed interpretation = overlapping train--index resamplings of the same 9,144-image corpus, not independent external replications

## Scientific closure already integrated
- session-volume side-channel analysis and traffic-shaping extensions;
- detector reporting based on descriptive means/ranges across five seeded resamplings, with 20 image-disjoint repeated splits used as within-resampling stability diagnostics;
- SOTA positioning with recovery-event semantics separated explicitly;
- public repository traceability;
- explicit necessity/sufficiency proof for finite-index feasibility;
- RS-parity reporting based on recoveries, communication cost, and paired gain/loss counts without independence-based confidence intervals or McNemar significance claims;
- verified Guo--Ping and Cao--Wang--Zhang bibliographic metadata;
- exact symbol-wise balancing attributed to the cyclic authenticated-session shift; Gray indexing specifies implementation ordering;
- ScholarOne metadata and Cover Letter synchronized to the seeded-resampling interpretation.

## Canonical A4 lineage gate
Canonical recheck workflow: **GitHub Actions run 35452993368**.

The workflow regenerates all five Caltech checkpoints under the frozen scientific environment, compares each SHA-256 with the recorded fresh-campaign hash, reruns authenticated channel recovery and the component ablation, then publishes one manifest per seed. A4 is closed only if every SHA check passes and the canonical manuscript-facing recovery totals remain consistent.

## Final release gate
Before A8:
1. A4 canonical checkpoint/result verification must pass.
2. A3 authenticated-control evidence must be integrated in the manuscript.
3. The final branch head must pass TOMM source validation after all editorial edits.
4. Only then may the branch be merged to `main` and an immutable ARCIS/TOMM release be created.

The final release commit, validation run, tag, and release URL are recorded here only after those operations succeed.
