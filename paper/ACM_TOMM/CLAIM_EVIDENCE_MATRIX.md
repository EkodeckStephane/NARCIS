# ARCIS — Claim/Evidence Matrix for TOMM

Scientific submission snapshot: `254f31e7c44e43f104509c117b0efb4c414dcdcd`  
Validation run: `35460375489` (**SUCCESS**)

| Major claim | Direct evidence | Scope / limitation |
|---|---|---|
| External authenticated recovery is 1,163/1,200 (96.92%) | `tomm_results/caltech_external_holdout_aggregate.json`; A4 audit | Five seeded Caltech train--index resamplings overlap; result is not five independent external replications |
| All 37 holdout failures occur at 12% crop | canonical holdout aggregate | Applies only to the declared holdout attack parameterizations |
| Control plane authenticates metadata and enforces freshness | `A3_AUTHENTICATED_CONTROL_PLANE_AUDIT.json` | 150/150 roundtrips; 5/5 tested tamper, replay, wrong-receiver cases rejected |
| RS128 improves reliability at traffic cost | `rs_parity_ablation_summary.json`; `communication_cost.json` | Paired gain/loss counts are descriptive under repeated attacks and overlapping resamplings |
| Complementary qualified grouping is the principal tested recovery contributor | `A5_CANONICAL_COMPONENT_ABLATION.json`; raw A5 CSV archive | Full 1,163; random groups 1,042; matched bucket 1,038; no claim that every component improves recovery |
| Cyclic mapping supports balancing | A5 fixed-mapping ablation; exact cycle argument in manuscript | Fixed mapping has slightly higher recovery (1,166), so cyclic mapping is not claimed as a recovery booster |
| Finite-index feasibility is explicit | necessity/sufficiency argument; `finite_index_blocking_risk.json` | Blocking probabilities are conditional on the stated planning model |
| Selection detectability is low but nonzero under tested wardens | `detector_resampling_summary.json` | SRM-lite/GLCM/CNN scope only; resampling means are descriptive |
| Guo--Ping 2026 is the closest recent natural-image selection comparator | complete KBS primary source; `GUO_PING_2026_SOURCE_AUDIT.json` | Its robustness is per representative/segment, not authenticated whole-message recovery |
| Guo--Ping source-native carrier counts are far smaller | Eqs. (29)--(31) in source; derived counts in manuscript | Raw-message counts exclude ARCIS AEAD/FEC/majority overhead; not a like-for-like throughput score |
| ARCIS contribution is integrated finite-index authenticated signaling | method, feasibility argument, A3/A4/A5 evidence | AES-GCM, HMAC and Reed--Solomon are standard components, not claimed as novel primitives |
| Public artifact is reproducible at the submission snapshot | commit `254f31e7c44e43f104509c117b0efb4c414dcdcd`, hashes, validators, GitHub Actions | Publication tag/release deferred until acceptance |

No claim in the current manuscript depends on the historical K=16 lineage.
