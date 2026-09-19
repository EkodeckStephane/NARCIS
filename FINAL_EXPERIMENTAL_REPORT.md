# ARCIS Final Experimental Report — ACM TOMM submission snapshot

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

## Canonical A5 component ablation
The A5 experiment was rerun on the byte-identified A4 lineage. The full ARCIS arm reproduces the canonical result exactly: **1,163/1,200**.

| Variant | Authenticated recovery | ARCIS-only gains / reverse gains |
|---|---:|---:|
| ARCIS full | 1,163/1,200 (96.92%) | reference |
| Random groups | 1,042/1,200 (86.83%) | 121 / 0 |
| Uniform group scheduler | 1,160/1,200 (96.67%) | 10 / 7 |
| Fixed mapping | 1,166/1,200 (97.17%) | 3 / 6 |
| Matched bucket baseline | 1,038/1,200 (86.50%) | 125 / 0 |

The recovery difference is concentrated in crop conditions. Complementary qualified grouping is therefore the principal recovery contributor among the tested mechanisms. The fixed-mapping result does not support a recovery-gain claim for cyclic mapping; instead, cyclic mapping reduces mean label-emission CV from **0.1314** to **0.0225** and makes every coded symbol visit all eight visual clusters over a complete cycle.

## Guo–Ping 2026 primary-source comparator
The complete Knowledge-Based Systems article is now audited. It specifies PZM features, SA-PQE, K-means CID construction, stability-regularized representative selection, and the main parameters **N=18, J=128, Δ=40, (w_center,w_stab)=(0.7,0.3)**. Its native robustness is per-representative message-segment recovery. Reported mean robustness at theoretical maximum capacity is **99.54% at 10 bits on Holidays, 98.64% at 14 bits on VOC 2012, and 97.19% at 15 bits on ImageNet**.

Its source-native hiding rule requires `ceil(P/L)+1` images for a P-bit raw message, giving 8/27/53 images at L=10, 6/20/38 at L=14, and 6/19/36 at L=15 for 8/32/64-byte payloads. Those counts exclude ARCIS cryptographic framing, metadata, RS parity, and five-cover majority overhead and are not treated as a like-for-like throughput score.

The paper does not freeze enough low-level details for a bit-identical independent executable reproduction; the repository records these limitations in `tomm_results/GUO_PING_2026_SOURCE_AUDIT.json`.

## SOTA positioning
Guo--Ping and ARCIS are positioned through their native quantitative regimes and recovery-event definitions, now grounded in the complete 2026 primary source. ARCIS success is exact authenticated whole-plaintext recovery after majority decoding, RS correction, framing, and AES-GCM verification. Guo--Ping's published robustness percentages remain under the source paper's native robustness metric and are not placed on a common percentage scale with ARCIS.

## Canonical-lineage closure
**A4 PASS.** The archived `NARCIS_TOMM_FRESH_CHECKPOINTS.zip` has SHA-256 `8193bb8462d5b79fb18462e8e55091b8982752161ed388e95b7b7785483ed1f1`. Its five Caltech checkpoints match the SHA-256 values recorded in the fresh campaign, and the archived runtime is Python 3.13.5 / PyTorch 2.10.0+cpu with the recorded scientific-package versions. The canonical holdout aggregate has SHA-256 `27f99fa00e9e8a7f1792195799615e8c8235718fa613fc20476a9f6014c70fcf` and yields exactly **1,163/1,200** with per-seed successes **240, 214, 240, 231, 238**.

A later retraining under a different runtime produced non-identical checkpoint bytes and is therefore classified as a diagnostic rather than as a replacement lineage.

## Submission-control status
The scientific submission snapshot was merged to `main` at commit `254f31e7c44e43f104509c117b0efb4c414dcdcd` and passed TOMM revision validation run `35460375489`. **A8 is therefore closed for submission.** A tag/release is deferred until post-acceptance version freezing.
