# ARCIS D1--D7 closure status

- **D1 — session-volume side channel:** CLOSED in the threat model and Discussion. The manuscript now treats image-content discrimination and observable session volume as separate layers and quantifies the 2,320 / 2,640 / 3,070-image RS128 cost.
- **D2 — correlated detector repetitions:** CLOSED. The five Caltech runs are treated as seeded train--index resamplings of one corpus, not independent external replications. Twenty repeated image-disjoint splits within each resampling quantify split stability, and detector means/ranges are reported descriptively. The classical detectors were rerun on the same certified final schedule used by the CNN audit (GitHub Actions run 35349137812).
- **D3 — closest SOTA comparison:** CLOSED editorially without a false numerical equivalence. Table 1 reports Guo--Ping's native 10/14/15-bit regime and makes recovery-event semantics explicit; ARCIS whole-message authenticated recovery remains separate.
- **D4 — artifact location:** CLOSED. The public repository is https://github.com/EkodeckStephane/NARCIS; the validated TOMM submission snapshot is `main` commit `c3e58a157b0b3bfe58959436e2d02e46d09c40cb`, with final validation run `35455852993` SUCCESS.
- **D5 — feasibility sufficiency:** CLOSED by explicit necessity/sufficiency argument with label-wise injections and the pigeonhole converse.
- **D6 — RS dependence handling:** CLOSED. The five Caltech runs overlap and attacks repeat within sessions, so the current manuscript reports parity-level recoveries and paired gain/loss counts descriptively rather than applying independence-based confidence intervals or McNemar significance tests.
- **D7 — bibliographic status:** CLOSED. Guo--Ping: KBS 338 (2026), 115472, DOI 10.1016/j.knosys.2026.115472. Cao--Wang--Zhang: Cybersecurity 8 (2025), 115, DOI 10.1186/s42400-025-00423-z.

## Direction E'
Section 4.4 and the Discussion now attribute exact balancing to the cyclic session shift for any fixed bijection \(\sigma\); Gray order is presented as the implementation-level symbol ordering rather than the source of the invariant.
