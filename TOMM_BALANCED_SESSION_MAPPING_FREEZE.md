# NARCIS — Balanced Session Mapping Freeze

This record fixes the authenticated-session mapping used by the TOMM validation path. It supersedes the earlier per-session pseudorandom-shift formulation.

## Experimental sequence rule

The communication workload uses a globally unique authenticated session sequence across payload sizes. For the frozen 30-message workload:

- 8-byte plaintexts use sequences `0..9`;
- 32-byte plaintexts use sequences `10..19`;
- 64-byte plaintexts use sequences `20..29`.

This matches replay-protection semantics and prevents artificial sequence-number reuse between payload-size batches.

## Balanced keyed Gray rotation

Let the codebook size be the frozen power of two `K`. Derive a mapping subkey

```text
K_map = HMAC-SHA256(K_master, "cluster-mapping").
```

From `K_map`, derive once per protocol key:

```text
b = HMAC-SHA256(K_map, "mapping-base") mod K
r = LSB(HMAC-SHA256(K_map, "mapping-orientation"))
```

where `r` is a secret orientation bit that is fixed for the key. For authenticated session sequence `q`, define

```text
shift_q = (b + q) mod K.
```

For Gray symbol `g(pos)=pos xor (pos >> 1)`, map

```text
pi_q[g(pos)] = (shift_q + sign(r) * pos) mod K,
```

with `sign(r)=+1` in forward orientation and `-1` in reverse orientation.

Cover ordering is independently keyed through the cover-selection subkey and includes the authenticated sequence and protected payload in its context.

## Exact distribution property

For any fixed coded symbol and any `K` consecutive session sequences, `shift_q` visits every cluster exactly once. Because the orientation is fixed for the key, the symbol-dependent offset is constant over the cycle; therefore `pi_q` also visits every cluster exactly once for that symbol.

This property is exact rather than heuristic. It prevents persistent non-uniformity in the framed/Reed–Solomon coded symbol stream from being permanently assigned to a particular visual cluster while preserving Gray locality inside each session.

## Final TOMM operating point

The external-validation protocol is frozen at:

- `K=8` codebook labels;
- group size `5` with majority decoding;
- Reed–Solomon parity `128` bytes;
- 30 authenticated sessions with global sequences `0..29`.

The K=8 choice follows the BOSSBase method-development campaign and is frozen before any Caltech-101 outcome from this protocol is inspected.

## Audit note

An earlier implementation varied the forward/reverse orientation independently by session. That version did not mathematically guarantee exact K-session balancing for a fixed symbol. It was corrected before external Caltech-101 validation. Earlier K=8 BOSSBase outputs generated with the old mapping are retained as development diagnostics and are not treated as final TOMM validation results.
