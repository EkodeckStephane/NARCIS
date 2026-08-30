# NARCIS — TOMM Runtime Verification

This record documents executable checks performed before continuing the fresh TOMM validation campaign. It is a verification record, not a manuscript-results summary.

## Assets

- BOSSBase: 10,000 readable 512×512 grayscale images; source manifest hash already recorded in `TOMM_DATASET_PROVENANCE.md`.
- Caltech-101: 9,144 readable source images; source manifest hash already recorded in `TOMM_DATASET_PROVENANCE.md`.
- Fresh checkpoints: 10/10 present for seeds `11, 29, 47, 71, 101` on both datasets.
- Checkpoint SHA-256 values match `TOMM_FRESH_CAMPAIGN.md`.

## Split verification

For every one of the ten trained models:

- the saved `train_files_seed_*.txt` list was compared in exact order with the split regenerated from `numpy.random.default_rng(seed).permutation(...)`;
- BOSSBase uses 2,000 training + 8,000 index images;
- Caltech-101 uses 1,500 training + 7,000 index images;
- train/index intersection is empty for all ten partitions.

Result: **PASS (10/10)**.

## Training histories

Each `training_history_seed_*.csv` contains exactly five epochs and all numeric fields are finite. Endpoint losses agree with the values recorded in `TOMM_FRESH_CAMPAIGN.md`.

Result: **PASS (10/10)**.

## Cache fidelity

For BOSSBase seed 11, the first 16 images were independently rerun from the fresh checkpoint and compared with the cached arrays for:

- clean;
- JPEG quality 80;
- Gaussian noise sigma 5.

Maximum absolute embedding difference for all three cases: **0.0**.

Result: **PASS**.

## Reed–Solomon verification

The local RS compatibility path was tested for parity values 128, 144, and 152 bytes on TOMM-relevant frame sizes. Random error patterns were injected through the theoretical correction bound `floor(parity/2)`. Decoded bytes and reported errata counts matched the injected cases.

Result: **PASS**.

## Protocol keying correction

Audit found that an earlier TOMM runner path still supplied a public dataset/seed string to `NarcisProtocol` even though cover mapping is described as keyed. The TOMM branch now derives independent mapping and cover-selection HMAC keys from secret protocol key material and varies the Gray mapping by authenticated sequence number.

Local regression checks cover:

- bijectivity of every K=16 session mapping tested;
- Hamming and Reed–Solomon round trips;
- deterministic selection for identical payload/session context;
- diversification across distinct authenticated sequences.

Result: **PASS**.

## GLCM/IPW implementation verification

A syntax defect in the reconstructed local copy of `glcm.py` was found before detector execution and replaced with the versioned implementation. Checks now cover normalized symmetric GLCMs, finite five-component texture features, and the expected checkerboard-vs-constant complexity ordering. Synthetic IPW tests also confirm a reduction of standardized mean imbalance.

Result: **PASS**.

## Distribution-matched redesign

The previous hard 12/12 stable-pool design remains a diagnostic branch because transmitted-cover membership was detectable. A new protocol is frozen in `TOMM_DISTRIBUTION_MATCHED_SELECTION.md` before final detector outcomes are inspected.

Its clean-only scheduler has been unit-tested: on a synthetic 16-stratum case, the maximum absolute difference between a 200-cover emitted prefix and the full reference stratum proportions was 0.002.

The real-data search uses BOSSBase seed 11 as the method-development partition. Remaining BOSSBase and all Caltech-101 partitions are reserved for validation without retuning.