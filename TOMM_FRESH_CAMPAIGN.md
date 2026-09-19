# NARCIS — Fresh TOMM Campaign Record

This file records the fresh retraining campaign initiated after the original BOSSBase and Caltech-101 source archives became available again. It does **not** contain final TOMM outcome claims. Numerical manuscript conclusions remain frozen until qualification, payload, detectability, and claim/data audits are complete.

## Dataset verification

The source archives were validated before retraining. Detailed archive and image-manifest hashes are recorded in `TOMM_DATASET_PROVENANCE.md`.

- BOSSBase 1.01: 10,000 readable PGM images, 512×512, grayscale.
- Caltech-101: 9,144 readable images across the extracted category tree. Source modes comprise RGB and grayscale images; the experimental loader converts the channel input uniformly to RGB before the 256×256 channel fit.

No corrupt source image was observed in the validation pass.

## Fresh retraining protocol

Frozen seeds: `11, 29, 47, 71, 101`.

- BOSSBase: 2,000 training images per seed; remaining 8,000 disjoint images form the cover index for that seed.
- Caltech-101: 1,500 training images per seed; 7,000 disjoint images form the cover index for that seed.
- encoder boundary: 128×128;
- embedding dimension: 64;
- base channels: 16;
- epochs: 5;
- batch size: 16;
- optimizer: AdamW, learning rate `1e-3`, weight decay `1e-5`;
- training augmentations: the versioned `ChannelAugment` path on `tomm-revision`;
- environment observed for the fresh campaign: PyTorch 2.10.0 CPU execution.

The fresh run is treated as a new training campaign rather than a bit-for-bit reconstruction of the historical IEEE-era checkpoints.

## Fresh checkpoint SHA-256

### BOSSBase

| Seed | SHA-256 |
|---:|---|
| 11 | `cbae789ea51aa991e49f50f11c0f631f44629036a8222464e0fb82ec11e1f123` |
| 29 | `98e7f077ed595a09ed2d3078648d560162129187f82d53a36f07359e09e8b89a` |
| 47 | `fcc28a8a444c529b31e1f3922d62cb06e7b1f4b67c624a2d7642033a45c2fe12` |
| 71 | `4c6442c4b76e8e4dcb3d4f404eaf7a2d1044e5da0535eabdd5d4317d19bce3b6` |
| 101 | `322a12ae7402f5c77a149c12bb636cd05c419636471fb4894c9511a3c98bc27a` |

### Caltech-101

| Seed | SHA-256 |
|---:|---|
| 11 | `0adac1e014b799ada4a46698bcad922ce4ce116697186c1d45964e405a81e28c` |
| 29 | `658e97d5fe4ad8da03ebad42461bce458d967beaf5753ac5d22a3c62eb480f2e` |
| 47 | `426d058567fbb08eca9a34668c1a20caeb29ba8d5c7b6ba0d2e8c44c449c6a2a` |
| 71 | `e0e958faf040a4d080d377a7694ea86cd602eab7c5350d4f04e619ca37fcade4` |
| 101 | `810f843f82cd6726b16ae632d38ec6bb0f1dbfaaf0345ffd92a6a0a883cb722e` |

## Fresh training endpoint losses

These are training diagnostics, not communication-performance results.

| Dataset | Seed | Epoch-5 loss |
|---|---:|---:|
| BOSSBase | 11 | 0.063485 |
| BOSSBase | 29 | 0.140765 |
| BOSSBase | 47 | 0.076578 |
| BOSSBase | 71 | 0.087347 |
| BOSSBase | 101 | 0.051647 |
| Caltech-101 | 11 | 0.132572 |
| Caltech-101 | 29 | 0.094015 |
| Caltech-101 | 47 | 0.098560 |
| Caltech-101 | 71 | 0.094834 |
| Caltech-101 | 101 | 0.076250 |

All ten five-epoch runs completed with finite losses.

## Qualification now required

Each checkpoint must pass the same preregistered TOMM qualification procedure before use in the final end-to-end experiment:

1. clean embeddings for the complete frozen cover index;
2. twelve calibration attacks only;
3. 16 principal + 32 deterministic random projection candidates;
4. calibration-locked projection ranking;
5. stable-cover finite-index feasibility at `K=16`;
6. stabilized inverse-probability weighting and SMD/ESS diagnostics;
7. projection and weighting locked before holdout/detectability evaluation.

The current campaign must not be summarized in the TOMM manuscript until all ten partition outputs and the later 8/32/64-byte image-channel and detector outputs are complete and audited.
