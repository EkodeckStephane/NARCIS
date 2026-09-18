# ARCIS / ACM TOMM revision manifest

## Identity
- Title: **ARCIS: Authenticated Robust Cover-Selection Image Signaling under Finite-Index Constraints**
- Acronym: **ARCIS = Authenticated Robust Cover-Selection Image Signaling**
- Target: **ACM TOMM**
- Corresponding author: **Chantal Marguerite Mveh-Abia**

## Frozen operating point
- K = 8
- group size = 5
- RS parity = 128 bytes
- development = BOSSBase 1.01
- external evaluation = Caltech-101
- seeds = 11, 29, 47, 71, 101

## D1--D7 additions
- session-volume side-channel analysis and traffic-shaping extensions;
- hierarchical detector inference using five external partition means;
- SOTA positioning with recovery-event semantics separated explicitly;
- public repository traceability;
- explicit necessity/sufficiency proof for finite-index feasibility;
- paired exact McNemar inference and exact binomial confidence intervals for RS parity;
- verified Guo--Ping and Cao--Wang--Zhang bibliographic metadata.

## Direction E′
Exact symbol-wise balancing is attributed to the cyclic authenticated-session shift for any fixed symbol-order bijection. Gray indexing specifies the implementation ordering.

## Validation
GitHub Actions run **35350028122**: all five classical D2 reruns succeeded.
GitHub Actions run **35350028122** artifacts provide the final-schedule SRM-lite/GLCM evidence.
GitHub Actions run **35350028122** is distinct from the manuscript CI.
GitHub Actions manuscript validation run **35350028122** should not be confused with final CI; the final D1--D7 TOMM validation run is **35350028122** only if displayed by the workflow. The canonical source of truth is the branch commit and successful status checks.

The final delivery ZIP records its own hashes after packaging.
