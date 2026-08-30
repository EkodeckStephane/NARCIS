# NARCIS — Session-Derived Mapping Freeze

## Motivation

Before inspecting detector outcomes for the full-corpus uniform experiment, the coded-symbol stream was audited directly. The outer RS framing contains deterministic structure (magic, length, CRC), so the empirical 4-bit symbol distribution over the frozen 8/32/64-byte workload is close to but not exactly uniform.

A single fixed symbol→cluster permutation could convert that small protocol-level symbol imbalance into a persistent visual-cluster imbalance across many messages.

## Frozen correction

For each authenticated session sequence `q`, derive a session mapping key from the master cover-selection key:

```text
K_q = HMAC-SHA256(K_master, "mapping-session" || uint64_be(q))
```

Instantiate the existing NARCIS keyed Gray permutation and HMAC cover ordering from `K_q` for that session.

Properties:

- the Gray/locality construction is preserved within each session;
- deterministic frame-symbol biases are pseudorandomly reassigned across visual clusters from session to session;
- sender and receiver can derive the same mapping before payload recovery because the sequence number belongs to authenticated session metadata;
- no image feature, semantic label, attack result, detector score, MMD value, or holdout outcome enters the derivation.

## Experimental rule

The full-corpus uniform experiment must use session-derived mapping for every message before support-level or traffic-level detectability is evaluated.

This addendum was frozen from the coded-symbol distribution audit, not from steganalysis outcomes of the new full-corpus design.
