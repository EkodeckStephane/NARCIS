# NARCIS — Balanced Session Mapping Freeze

This document refines `TOMM_SESSION_KEY_FREEZE.md` before any detector result from the full-corpus uniform design is inspected.

## Experimental sequence correction

The previous campaign helper generated sequence values `0..9` independently for each payload-size batch. The TOMM campaign instead assigns a **globally unique authenticated session sequence** across the complete workload. For the frozen 30-message workload:

- 8-byte messages: sequences 0–9;
- 32-byte messages: sequences 10–19;
- 64-byte messages: sequences 20–29.

This matches replay protection semantics and prevents artificial session-number reuse.

## Balanced keyed Gray rotation

Let `K=16`. Derive a secret base rotation

```text
b = HMAC-SHA256(K_master, "mapping-base") mod K.
```

For authenticated session sequence `q`, define

```text
shift_q = (b + q) mod K
reverse_q = LSB(HMAC-SHA256(K_master, "mapping-orientation" || uint64_be(q)))
```

For Gray symbol `g(pos)=pos xor (pos >> 1)`, map

```text
pi_q[g(pos)] = (shift_q + sign(reverse_q) * pos) mod K,
```

where the sign is +1 in forward orientation and −1 in reverse orientation.

The cover-ordering key is independently derived from the master key and sequence.

## Distribution property

For any fixed coded symbol and any block of `K` consecutive session sequences, `shift_q` visits every cluster exactly once. Consequently, persistent non-uniformity in the framed/RS-coded symbol stream is not permanently assigned to one visual cluster. The reverse bit retains keyed orientation diversity while the cyclic shift supplies exact long-run cluster balancing.

This mechanism preserves Gray locality within every session and uses no image statistics, semantic labels, attacks, detector scores, holdout results, or MMD objective.

## Supersession

For the TOMM full-corpus experiment, this balanced cyclic mapping supersedes the purely pseudorandom session-shift formulation in `TOMM_SESSION_KEY_FREEZE.md`.
