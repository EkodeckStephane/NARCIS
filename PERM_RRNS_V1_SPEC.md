# ARCIS Local-Permutation RRNS v1.0 — Frozen Development Specification

Status: **frozen before fresh holdout**. This document specifies the method to be evaluated next. The earlier 400/400 Caltech result is development evidence only because the old holdouts informed decoder design.

## 1. Scope and invariants

The method preserves the ARCIS K=8 balanced label channel and five-cover complementary groups, but adds a local order channel and replaces RS128 with a residue-number code. Pixel values are never modified. Each transmitted group contains five distinct covers selected from one canonical ARCIS group bank. Within-session cover reuse is forbidden.

For every residue `r < 512`, write `r = 64*a + p`, with `a in [0,7]` and `p in [0,63]`. The 3-bit value `a` is carried by the ARCIS cluster symbol; `p` is a Myrvold–Ruskey rank selecting one of the first 64 permutations of S5. Thus one five-cover group carries one 9-bit residue without changing any image.

## 2. Compact authenticated payload

For a plaintext of P bytes, derive the 256-bit AES-GCM key as `HMAC-SHA256(master_key, "payload-encryption")`. The 96-bit nonce is `HMAC-SHA256(master_key, "nonce-prefix")[:4] || uint64(sequence)`. The associated data is `NARCIS-PAYLOAD-1 || uint64(sequence)`.

Only `ciphertext || 128-bit GCM tag` is sent through the covert image channel; the nonce is reconstructed by Bob. Consequently the covert protected length is `P + 16` bytes. Nonce uniqueness requires that a sequence number is never reused under one master key, including after restart or rollback. Replay protection therefore remains mandatory.

## 3. RRNS construction

The modulus universe is the 97 primes below 512. For redundancy r=18, choose the smallest k such that the product of the k smallest moduli in the selected n=k+r largest primes spans the complete source interval. Equivalently, the conservative capacity satisfies `sum(log2(m_i), i=1..k) >= 8*source_bytes`.

Frozen traffic points:
- 8-byte plaintext -> 24 protected bytes -> k=23, r=18, n=41 -> **205 images**.
- 32-byte plaintext -> 48 protected bytes -> k=49, r=18, n=67 -> **335 images**.
- 64-byte plaintext -> 80 protected bytes -> two minimum-cost RRNS blocks -> **580 images** total.

The guaranteed unknown-residue error radius of one r=18 block is 9. The implemented robust candidate generator uses CRT plus continued-fraction reconstruction; AES-GCM is the final acceptance oracle.

## 4. Payload-independent group synchronization

Group selection must be reconstructible before decoding the hidden residue. For each cluster label, its group-bank indices are ordered by HMAC under the domain `local-permutation-group-schedule-v1` using `(sequence,label,group_index)`. At global residue position j, Alice and Bob use the j-th scheduled group of the candidate label. This removes the circular dependency that existed when group selection depended on the payload hash.

The global residue position is never reset between RRNS blocks. The current Caltech banks contain 175 groups per label, so the frozen 8/32/64-byte points use at most 116 global positions and remain within the no-reuse budget.

## 5. Joint cluster–permutation decoder

The decoder does not first hard-decide a cluster. For each received five-cover group and each candidate cluster symbol, it reconstructs the scheduled canonical five-cover group, compares received embeddings with calibration-only reference templates, and scores all valid local permutation ranks. It retains the best four residue candidates.

Two template hypotheses are frozen and tried independently, with acceptance only after successful AEAD verification:
1. **crop hypothesis**: normalized clean, crop-5%, midpoint of crop-5/crop-10 embeddings, crop-10%, and linear extrapolation `2*crop10-crop05`;
2. **general hypothesis**: normalized clean plus all twelve frozen calibration attacks.

No fresh-holdout data may be used to change these templates, the list size, beam width, beam depth, RRNS parameters, ranking rule, group schedule, or AEAD construction.

## 6. Beam/list-RRNS decoding

For each residue, the top-ranked candidate forms the hard vector. The robust RRNS decoder is tried first. If no AEAD-valid reconstruction exists, residue positions are ordered by the score gap between their first two candidates. At most the twelve least-certain positions are opened. The beam width is 600. Alternative choices are ranked by accumulated score loss. Every reconstructed protected byte string is accepted only if AES-GCM authentication succeeds.

Frozen decoder constants: candidate list size 4, beam positions 12, beam width 600, K=8, group size 5, permutation ranks 0..63, RRNS r=18.

## 7. Development evidence and evidentiary boundary

The exploratory Caltech campaign obtained 400/400 accepted 8-byte sessions across Gaussian 9/15, blur 1.2/1.8, crop 8/12%, and rotation 5/9%, with 205 images per session. These attacks are now development data for this new method. They must not be called fresh holdout evidence in any manuscript.

No TOMM claim, table, abstract, Gate-10 status, or canonical A4/A5 evidence is changed by this branch until the fresh pre-registered campaign passes and a new claim/code/data audit is completed.

## 8. Required fresh validation outputs

The next campaign must report, for 8/32/64-byte payloads: exact authenticated recovery, images/session, useful bit/image, RRNS top-1 residue errors, hard versus beam recovery, candidate states tested, decoding time, cover reuse, per-attack results, failure diagnostics, and sequential detectability. Loss, duplication, and reordering tests are reported separately from visual-channel attacks.
