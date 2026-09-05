# NARCIS — Aligned Final Channel Recheck Freeze

This record is frozen before inspection of any result produced by `tools/tomm_final_channel_recheck.py`.

## Rationale

The final multi-session detector audit reconstructs a canonical, machine-independent Caltech-101 schedule using relative POSIX image identifiers. Historical aggregate channel results were produced before that canonical identifier normalization and therefore cannot, by themselves, prove recovery for the exact schedule evaluated by the final SRM-lite/GLCM/CNN audit.

To keep the final manuscript's robustness and detectability claims on one claim/code/data lineage, the authenticated image channel is re-evaluated on the same five canonical Caltech-101 partitions and the same final K=8 group-bank schedule before detector results are consolidated.

## Frozen method

No NARCIS method parameter changes. The recheck uses the already frozen final protocol:

- partition seeds `11, 29, 47, 71, 101`;
- 1,500 representation-training images and 7,000 disjoint index images per partition;
- canonical cover identifiers equal to paths relative to the dataset root with POSIX separators;
- K=8 one-dimensional balanced quantile codebook;
- 16 principal + 32 deterministic random projection candidates;
- projection seed `20260828 + partition_seed`;
- calibration attacks: JPEG 80/50, Gaussian 5/12, blur 0.8/1.5, resize 0.75/0.50, crop 0.05/0.10, rotation 3/7 degrees;
- group size 5, strict majority;
- group-bank seed `20260830 + partition_seed`, 10 restarts, 6,000 swaps per restart;
- Reed–Solomon parity 128 bytes;
- deterministic 8/32/64-byte workloads, ten authenticated messages per payload size, sequences 0..29;
- the existing balanced cyclic keyed Gray mapping and group-signature scheduler.

## Holdout attacks

The following already versioned holdout transformations in `src/narcis/attacks.py` are evaluated without entering projection or group-bank construction:

- Gaussian sigma 9 and 15;
- Gaussian blur radius 1.2 and 1.8;
- crop fractions 0.08 and 0.12;
- rotations 5 and 9 degrees.

The holdout family remains evaluation-only. No holdout outcome may change the projection, group bank, FEC, mapping, schedule, or detector protocol.

## Output and interpretation

For every partition, preserve every session × attack observation with exact authenticated plaintext success, Reed–Solomon correction count, cover-label accuracy, payload size, and cover count. Calibration and holdout failures, if any, remain in the record.

The recheck must persist and verify the exact `schedule.csv` and `session_target.npy` shared with the final detector audit. A schedule mismatch is a hard audit failure; it is not repaired by changing NARCIS parameters.

The earlier 1,800/1,800 calibration aggregate remains historical evidence. The final TOMM manuscript will use the aligned canonical recheck for claims that are combined with the new multi-session detectability audit.
