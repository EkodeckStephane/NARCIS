# NARCIS — Final TOMM Claim / Code / Data Audit

**Target:** ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)  
**Title:** *NARCIS: Authenticated Neural Coverless Image Signaling with Attack-Qualified Codebooks and Error Correction*  
**Final author order:** Arthur Ulrich Ewane; Stéphane Gaël R. Ekodeck; Serge Alain Ebélé; Vivien Loïck Beyala Kamgang; Chantal Marguerite Mveh-Abia (corresponding author).

## Canonical experimental lineage

The manuscript uses only the externally frozen TOMM lineage: `K=8`, balanced one-dimensional quantile codebook, five covers per coded symbol, strict majority decoding, RS128, 30 authenticated sessions per partition, payload lengths 8/32/64 bytes, seeds 11/29/47/71/101, balanced cyclic keyed Gray mapping, and the signature-balanced group-bank scheduler. BOSSBase is a development corpus; Caltech-101 is the external validation corpus. Historical K=16 / 1,575-trial values are excluded from manuscript-facing claims.

Canonical evidence files:
- `tomm_results/caltech_external_calibration_aggregate.json`
- `tomm_results/caltech_external_holdout_summary.json`
- `tomm_results/final_detector_summary.json`
- `tomm_results/diffstega_reproduction_summary.json`
- frozen protocol/audit documents in the repository root.

## Promise–evidence matrix

| Manuscript promise | Evidence | Final status |
|---|---|---|
| Calibration-locked finite-index signaling is feasible on all five external partitions | External calibration aggregate; 30 sessions/seed | **Demonstrated under frozen protocol** |
| Calibration authenticated recovery is 1,800/1,800 | 5 seeds × 30 sessions × 12 attacks | **Demonstrated** |
| External holdout authenticated recovery is 1,163/1,200 (96.92%) | Holdout summary | **Demonstrated** |
| All 37 holdout failures occur under 12% central crop | Holdout by-attack record | **Demonstrated boundary condition** |
| Seven other holdout transformations are 150/150 each | Holdout by-attack record | **Demonstrated under declared channel** |
| SRM-lite mean macro-AUC is 0.504048 | `final_detector_summary.json` | **Demonstrated; near chance** |
| GLCM mean macro-AUC is 0.512833 | same | **Demonstrated; weak measurable signal** |
| CNN mean macro-AUC is 0.526603 | same + 100 repetition rows / 3,000 per-head rows | **Demonstrated; modest systematic signal** |
| NARCIS is “undetectable” | contradicted by CNN/GLCM audit | **Excluded** |
| Official DiffStega 100-case execution completed | evidence bundle; frozen upstream commit; 700 PNG outputs; zero evaluation errors | **Demonstrated** |
| DiffStega correct-recovery PSNR is reproduced at 23.274 dB | independent frozen evaluator | **Independently reproduced metric** |
| Exact reproduction of every DiffStega paper metric | paper metric scripts absent upstream; two metric-only version deviations | **Not claimed** |
| NARCIS numerically outperforms DiffStega | information objects and metrics differ | **Excluded** |
| Universal robustness / universal steganalysis resistance | finite channel and detector models; crop boundary | **Excluded** |
| Production KMS / deployment / traffic-analysis security | not evaluated | **Excluded** |

## Numerical cross-check

### Caltech external calibration
- 5 partitions × 30 sessions × 12 attacks = **1,800 trials**.
- Authenticated recoveries: **1,800/1,800**.
- Maximum RS corrections: **37**.
- Stable-cover counts by seed: 4,184; 3,795; 4,756; 3,933; 4,167.

### Caltech external holdout
- 5 partitions × 30 sessions × 8 attacks = **1,200 trials**.
- Authenticated recoveries: **1,163/1,200 = 96.92%**.
- `crop_12_holdout`: **113/150**; exactly **37 failures**.
- All seven other holdouts: **150/150**.
- Maximum RS corrections: **64**.

### Detectability
Each detector has **100 repeated image-disjoint splits** (5 seeds × 20 repeats).
- SRM-lite + ExtraTrees: mean **0.5040483434**, SD **0.0022639481**.
- GLCM + logistic: mean **0.5128334840**, SD **0.0017180488**.
- 30-head CNN: mean **0.5266028248**, SD **0.0033869841**.
Repeated-split intervals are descriptive; no naive confirmatory one-sample t-test is used because the splits overlap.

### DiffStega
- Upstream commit: `73cd7cb8d102f4fc0f5bb168a71cfb948077d89a`.
- Official UniStega cases: **100/100 complete** (30 similar + 42 content + 28 style).
- Output PNGs: **700**; evaluation errors: **0**.
- Correct-recovery PSNR: **23.274238 dB** vs. **23.290 dB** published.
- Evidence SHA-256: `32d0e975eb197adb0d1d2f7c537b04b4fab84af45a51148eaf15872b40de1f46`.
- Metric-only environment deviations retained: `huggingface-hub` 0.36.2 vs 0.20.3 and `pyiqa` 0.1.15 vs 0.1.13. They do not alter the frozen DiffStega generation benchmark.

## Manuscript consistency checks

- Exact title and final author order synchronized; René Ndoundam removed.
- No K=16 / 1,575-trial historical result appears in the final manuscript.
- BOSSBase is explicitly development-only; Caltech-101 carries the external claims.
- “Undetectable”, “universal robustness”, “state of the art”, and direct DiffStega superiority are not manuscript claims.
- All manuscript-facing headline numbers map to canonical machine-readable evidence.
- The final local LaTeX build has no undefined citation/reference and no overfull-box warning.

## Final audit verdict

**CLAIM / CODE / DATA = PASS.**

The final manuscript is aligned with the frozen code/data evidence. Residual limitations—12% crop failures, CNN selection signal, one untouched external corpus, finite warden family, and independent DiffStega metric implementation—are disclosed scientific boundaries rather than hidden contradictions.
