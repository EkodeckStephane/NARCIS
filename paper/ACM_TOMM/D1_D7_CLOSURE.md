# ARCIS D1--D7 closure status

- **D1 — session-volume side channel:** CLOSED in the threat model and Discussion. The manuscript now treats image-content discrimination and observable session volume as separate layers and quantifies the 2,320 / 2,640 / 3,070-image RS128 cost.
- **D2 — correlated detector repetitions:** CLOSED. Inference now uses five external partition means; 20 repeated image-disjoint splits per partition are stability diagnostics. The classical detectors were rerun on the same certified final schedule used by the CNN audit (GitHub Actions run 35349137812).
- **D3 — closest SOTA comparison:** CLOSED editorially without a false numerical equivalence. Table 1 reports Guo--Ping's native 10/14/15-bit regime and makes recovery-event semantics explicit; ARCIS whole-message authenticated recovery remains separate.
- **D4 — artifact location:** CLOSED. The public repository is https://github.com/EkodeckStephane/NARCIS and the D1--D7 repair is traceable on branch `arcis-tomm-d1-d7`.
- **D5 — feasibility sufficiency:** CLOSED by explicit necessity/sufficiency argument with label-wise injections and the pigeonhole converse.
- **D6 — RS paired inference:** CLOSED with exact Clopper--Pearson intervals and exact paired McNemar tests with Holm adjustment.
- **D7 — bibliographic status:** CLOSED. Guo--Ping: KBS 338 (2026), 115472, DOI 10.1016/j.knosys.2026.115472. Cao--Wang--Zhang: Cybersecurity 8 (2025), 115, DOI 10.1186/s42400-025-00423-z.

## Direction E'
Section 4.4 and the Discussion now attribute exact balancing to the cyclic session shift for any fixed bijection \(\sigma\); Gray order is presented as the implementation-level symbol ordering rather than the source of the invariant.
