# ARCIS-PERM-RRNS v1 — Pre-analysis Fresh Holdout Protocol

This protocol is frozen before opening new holdout outcomes. The previous Gaussian 9/15, blur 1.2/1.8, crop 8/12%, and rotation 5/9% results are development evidence and cannot be reused as final holdout evidence for ARCIS-PERM-RRNS v1.

## Frozen method

Use `PERM_RRNS_V1_SPEC.md` unchanged: K=8, group size 5, 64 Myrvold–Ruskey local permutations, RRNS r=18, payload-independent HMAC group schedule, four residue candidates, twelve beam positions, beam width 600, crop and general calibration-only template hypotheses, and AES-GCM validation with a derived nonce.

## Fresh partition seeds

Use five new deterministic resampling seeds: **131, 157, 181, 211, 241**. Calibration remains limited to the original twelve calibration transforms. No result from the attacks below may influence projection selection, group-bank construction, template construction, RRNS selection, candidate-list size, beam parameters, or acceptance criteria.

## Fresh visual attacks

Evaluate the following previously unopened conditions: Gaussian sigma 7 and 18; Gaussian blur sigma 1.0 and 2.1; center crop 6%, 9%, and 14%; rotation 4, 6, and 11 degrees; JPEG quality 65; crop 9% followed by JPEG-65; crop 14% followed by blur-1.0. Random transforms use deterministic attack seeds derived from `(partition_seed, attack_name, image_index)` and must be regenerated from the native image, not from an already attacked image unless the composite attack explicitly says so.

## Payload workload

For each partition and each attack, transmit 10 independently sequenced sessions at each payload size 8, 32, and 64 bytes using the deterministic benchmark plaintext generator. Sequence values must never repeat under one benchmark master key. The primary unit is the authenticated session; seeded resamplings are not independent population replications and will not be used to construct independence-based confidence intervals.

## Primary endpoints

For each payload size and attack record: authenticated successes/trials; images/session; useful bits/image; hard-decoder successes; beam-decoder successes; mean/max candidate states tested; mean/max RRNS top-1 residue errors; decode latency; any cover reuse; and failure reason. Report per-seed values and pooled descriptive totals.

A session is successful only when the recovered plaintext is exactly equal to the transmitted plaintext and AES-GCM authentication succeeds. Invalid tags, ambiguous candidates, exhausted beam searches, missing groups, and malformed residue vectors are failures; they must never be silently repaired using ground truth.

## Separate network-order stress tests

After the visual holdout is closed, run loss/duplication/reordering tests as a distinct experiment: one missing image within a group, one duplicated image, adjacent-image swap, adjacent-group swap, and burst loss of 2/3/5 images. These tests must specify the framing mechanism used to delimit five-cover groups. They are not mixed with the visual attack success rate.

## Sequential detectability

Compare ordinary ARCIS transmission ordering against ARCIS-PERM-RRNS v1 using cluster-transition distributions, consecutive-cover embedding similarity, cover-frequency distribution, group-position statistics, and a sequence classifier trained only on development data. Final detectability is evaluated on the fresh partitions. Image-content SRM/GLCM/CNN results remain separate from this sequence-level test.

## Freeze rule

If any algorithmic or numerical parameter changes after any fresh-holdout result is inspected, the affected conditions become development data and a new unopened holdout must be defined before scientific claims are made.
