# NARCIS — Final TOMM Closure Record

## Closure decision

The experimental, scientific, and editorial closure required for the current manuscript claims is complete.

## Canonical protocol

- K=8 balanced one-dimensional quantile codebook.
- Five covers per coded symbol; strict majority decoding.
- Reed–Solomon parity: 128 bytes.
- 30 authenticated sessions per external partition: 10 each at 8/32/64 plaintext bytes.
- External seeds: 11, 29, 47, 71, 101.
- Balanced cyclic keyed Gray mapping.
- Calibration-failure-signature-balanced group scheduler.
- AES-GCM authenticated payload/session path with sequence-bound associated data and explicit benchmark nonce uniqueness.

## Frozen evidence

- Calibration: **1,800/1,800**.
- Holdout: **1,163/1,200 (96.92%)**; all 37 failures are `crop_12`.
- Detectability: SRM-lite **0.5040**; GLCM **0.5128**; CNN **0.5266** mean macro-AUC.
- DiffStega: **100/100** cases completed; correct-recovery PSNR **23.274 dB**; evidence SHA-256 `32d0e975eb197adb0d1d2f7c537b04b4fab84af45a51148eaf15872b40de1f46`.

## Final manuscript controls

- ACM `acmart` manuscript format.
- 13-page compiled review manuscript.
- No undefined references/citations.
- No overfull-box warnings.
- Figures include ACM `\Description{}` accessibility text.
- Title/author order synchronized.
- No stale K=16/1,575-trial result.
- No RQ/Phase/development-history narrative.
- Limitations contain the crop, detector, external-corpus, cryptographic, and comparator boundaries.

## Gate decision

**Q1 Gate 10: PASS for the stated study.**

This decision means the manuscript is internally claim-safe and ready for journal submission under its stated scope. It does not imply or predict editorial acceptance.
