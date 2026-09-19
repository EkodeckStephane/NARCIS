# ARCIS Final Experimental Report — ACM TOMM release candidate

## Frozen operating point
ARCIS uses `K=8`, five covers per coded symbol, and RS128 at the final operating point. BOSSBase 1.01 is the development corpus. Caltech-101 is the external corpus.

For each Caltech seed in `{11, 29, 47, 71, 101}`, a deterministic permutation assigns 1,500 images to descriptor training and the next 7,000 images to the cover index. Training and index sets are image-disjoint within each run. The five runs are seeded train--index resamplings of the same 9,144-image corpus, not independent external replications: pairwise index overlap is 5,320--5,371 images (76.0--76.7%), and 2,374 images occur in all five indexes.

## External recovery
- Calibration: **1,800/1,800** authenticated recoveries.
- Held-out attack parameterizations: **1,163/1,200 (96.92%)**.
- Seven of the eight held-out parameterizations: **150/150** each.
- 12% crop: **113/150**; all 37 holdout failures occur there.
- Per-resampling success: **240/240, 214/240, 240/240, 231/240, 238/240** for seeds 11, 29, 47, 71, 101.

## Authenticated control plane
The implemented metadata path was exercised over five seeds and 30 monotonically ordered sessions per seed:
- **150/150** exact metadata roundtrips;
- **5/5** tested ciphertext tamper cases rejected;
- **5/5** immediate replay attempts rejected;
- **5/5** wrong-receiver cases rejected through associated-data binding;
- metadata envelope size: **110–111 bytes**.

## RS-parity ablation
The same 1,200 resampling--session--attack outcomes are reused at every parity level.

| RS parity bytes | Authenticated recovery | Mean images/session | Paired gain/loss vs previous |
|---:|---:|---:|---:|
| 0 | 829/1,200 (69.08%) | 970.0 | — |
| 32 | 1,064/1,200 (88.67%) | 1,396.7 | 235/0 |
| 64 | 1,115/1,200 (92.92%) | 1,825.0 | 51/0 |
| 96 | 1,145/1,200 (95.42%) | 2,250.0 | 30/0 |
| 128 | 1,163/1,200 (96.92%) | 2,676.7 | 18/0 |

The RS0→RS128 endpoint contains **334 gains / 0 losses**. These counts are reported descriptively because attacks are repeated within sessions and the five Caltech runs overlap substantially; the current manuscript therefore does not treat the 1,200 outcomes or the five resamplings as independent inferential units.

## Communication and traffic observability
At RS128:
- 8 B → 2,320 images → 0.0276 useful bit/image.
- 32 B → 2,640 images → 0.0970 useful bit/image.
- 64 B → 3,070 images → 0.1668 useful bit/image.

The cover count therefore exposes payload-length-class information in an unshaped session. The manuscript treats fixed-volume batching, payload padding, dummy-cover insertion, timing shaping, denser group signaling, and adaptive parity as deployment extensions.

## Conditional finite-index planning
Under the stated i.i.d.-uniform coded-symbol planning model:
- 8 B: **5.04×10^-43**
- 32 B: **1.64×10^-34**
- 64 B: **1.14×10^-25**

The realized-session feasibility criterion remains `d_k <= a_k` for every label, with necessity and sufficiency stated label by label.

## Selection-detector audit
Each Caltech resampling uses 20 image-disjoint train/test repetitions. These repetitions quantify within-resampling split stability. The five resampling means are reported descriptively because their underlying image pools overlap.

| Detector | Mean AUC | Resampling range | Mean within-run SD |
|---|---:|---:|---:|
| SRM-lite + ExtraTrees | 0.5040 | 0.5014–0.5052 | 0.0018 |
| GLCM + logistic | 0.5128 | 0.5120–0.5138 | 0.0016 |
| 30-head CNN | 0.5266 | 0.5232–0.5301 | 0.0022 |

## SOTA positioning
Guo--Ping and ARCIS are positioned through their native quantitative regimes and recovery-event definitions. ARCIS success is exact authenticated whole-plaintext recovery after majority decoding, RS correction, framing, and AES-GCM verification. Guo--Ping's published robustness percentages remain under the source paper's native robustness metric and are not placed on a common percentage scale with ARCIS.

## Canonical-lineage closure
**A4 PASS.** The archived `NARCIS_TOMM_FRESH_CHECKPOINTS.zip` has SHA-256 `8193bb8462d5b79fb18462e8e55091b8982752161ed388e95b7b7785483ed1f1`. Its five Caltech checkpoints match the SHA-256 values recorded in the fresh campaign, and the archived runtime is Python 3.13.5 / PyTorch 2.10.0+cpu with the recorded scientific-package versions. The canonical holdout aggregate has SHA-256 `27f99fa00e9e8a7f1792195799615e8c8235718fa613fc20476a9f6014c70fcf` and yields exactly **1,163/1,200** with per-seed successes **240, 214, 240, 231, 238**.

A later retraining under a different runtime produced non-identical checkpoint bytes and is therefore classified as a diagnostic rather than as a replacement lineage.
