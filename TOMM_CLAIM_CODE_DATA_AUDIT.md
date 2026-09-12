# NARCIS — Final TOMM Claim / Code / Data Audit

**Target:** ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)  
**Title:** *NARCIS: Authenticated Neural Coverless Image Signaling with Attack-Qualified Codebooks and Error Correction*  
**Final author order:** Arthur Ulrich Ewane; Juvet Karnel Sadié; Stéphane Gaël R. Ekodeck; Serge Alain Ebélé; Vivien Loïck Beyala Kamgang; Damaris Belle M. Fotso; Chantal Marguerite Mveh-Abia (corresponding author).

## Canonical experimental lineage

The manuscript uses the frozen TOMM lineage: `K=8`, balanced one-dimensional quantile codebook, five covers per coded symbol, strict majority decoding, RS128, 30 authenticated sessions per partition, payload lengths 8/32/64 bytes, seeds 11/29/47/71/101, balanced cyclic keyed Gray mapping, and the signature-balanced group-bank scheduler. BOSSBase provides method-development evidence; Caltech-101 provides external validation. Historical K=16 / 1,575-trial values remain outside manuscript-facing claims.

Canonical evidence files:
- `tomm_results/bossbase_final_v2_development.json`
- `tomm_results/caltech_external_calibration_aggregate.json`
- `tomm_results/caltech_external_holdout_summary.json`
- `tomm_results/final_detector_summary.json`
- `tomm_results/diffstega_reproduction_summary.json`
- frozen protocol/audit documents in the repository root.

## Promise–evidence matrix

| Manuscript promise | Evidence | Final status |
|---|---|---|
| Frozen BOSSBase K=8 development lineage recovers 1,800/1,800 calibration messages | Development aggregate across five seeds | **Demonstrated as development evidence** |
| BOSSBase complete-schedule cover participation reaches 7,995–8,000 unique covers/seed | Development cover-use records | **Demonstrated** |
| Calibration-locked finite-index signaling is feasible on all five external partitions | External calibration aggregate; 30 sessions/seed | **Demonstrated under frozen protocol** |
| External calibration authenticated recovery is 1,800/1,800 | 5 seeds × 30 sessions × 12 attacks | **Demonstrated** |
| All 7,000 Caltech covers participate in every complete external schedule | External cover-use records | **Demonstrated** |
| External holdout authenticated recovery is 1,163/1,200 (96.92%) | Holdout summary | **Demonstrated** |
| The 12% crop contributes the 37 observed holdout failures | Holdout by-attack record | **Demonstrated boundary condition** |
| Seven other holdout transformations achieve 150/150 each | Holdout by-attack record | **Demonstrated under declared channel** |
| SRM-lite mean macro-AUC is 0.504048 | `final_detector_summary.json` | **Demonstrated; near chance** |
| GLCM mean macro-AUC is 0.512833 | same | **Demonstrated; weak measurable signal** |
| CNN mean macro-AUC is 0.526603 | same + 100 repetition rows / 3,000 per-head rows | **Demonstrated; modest systematic signal** |
| CNN signal persists across external partitions | Seed means 0.523150–0.530054 | **Demonstrated** |
| Official DiffStega 100-case execution completed | evidence bundle; frozen upstream commit; 700 PNG outputs; zero evaluation errors | **Demonstrated** |
| DiffStega correct-recovery PSNR is reproduced at 23.274 dB | independent frozen evaluator | **Independently reproduced metric** |
| Family-specific NARCIS/DiffStega metrics retain their native semantics | method/comparator definitions | **Claim-safe positioning** |

## Numerical cross-check

### BOSSBase development
- 5 seeds × 30 sessions × 12 attacks = **1,800 calibration trials**.
- Authenticated recoveries: **1,800/1,800**.
- Unique covers per seed: **8,000; 7,995; 8,000; 8,000; 8,000**.
- Development Global7 AUC mean across seeds: **0.5138647**.
- Development Clean15 AUC mean across seeds: **0.5183620**.
- Maximum calibration RS corrections: **7**.
- Seed-11 holdout diagnostic: **240/240**; crop-12 mean symbol accuracy **0.96285**; maximum RS corrections **25**.

### Caltech external calibration
- 5 partitions × 30 sessions × 12 attacks = **1,800 trials**.
- Authenticated recoveries: **1,800/1,800**.
- Maximum RS corrections: **37**.
- Stable-cover counts by seed: **4,184; 3,795; 4,756; 3,933; 4,167**.
- Stable fractions: **0.598; 0.542; 0.679; 0.562; 0.595**.
- Unique covers: **7,000/7,000 for every partition**.
- Mean cover-use frequency: **11.471**; frequency CV range **0.2276–0.2307**.

### Caltech external holdout
- 5 partitions × 30 sessions × 8 attacks = **1,200 trials**.
- Authenticated recoveries: **1,163/1,200 = 96.92%**.
- `crop_12_holdout`: **113/150**; **37 observed failures**.
- Seven other holdouts: **150/150** each.
- Maximum RS corrections: **64**.
- Per-seed success: **240/240; 214/240; 240/240; 231/240; 238/240**.

### Detectability
Each detector has **100 repeated image-disjoint splits** (5 seeds × 20 repeats).
- SRM-lite + ExtraTrees: mean **0.5040483434**, SD **0.0022639481**.
- GLCM + logistic: mean **0.5128334840**, SD **0.0017180488**.
- 30-head CNN: mean **0.5266028248**, SD **0.0033869841**.
- CNN seed means: **0.523150; 0.527023; 0.530054; 0.524239; 0.528548**.
Repeated-split intervals are descriptive because the splits overlap.

### DiffStega
- Upstream commit: `73cd7cb8d102f4fc0f5bb168a71cfb948077d89a`.
- Official UniStega cases: **100/100 complete** (30 similar + 42 content + 28 style).
- Output PNGs: **700**; evaluation errors: **0**.
- Correct-recovery PSNR: **23.274238 dB** versus **23.290 dB** published.
- Evidence SHA-256: `32d0e975eb197adb0d1d2f7c537b04b4fab84af45a51148eaf15872b40de1f46`.
- Metric-only environment deviations retained: `huggingface-hub` 0.36.2 vs 0.20.3 and `pyiqa` 0.1.15 vs 0.1.13.

## Manuscript consistency checks

- Exact title and seven-author order are synchronized in manuscript/status/cover-letter assets.
- Juvet Karnel Sadié carries the same three affiliations as Stéphane Gaël R. Ekodeck and has no ORCID entry.
- Damaris Belle M. Fotso carries her verified University of Yaoundé I/LIRIMA affiliation, email, and ORCID `0009-0001-8736-0644`.
- BOSSBase results are explicitly labeled development evidence; Caltech-101 carries external claims.
- Headline values map to canonical machine-readable evidence.
- The manuscript contains nine dedicated scientific figures and nine tables covering protocol structure, cyclic balancing, development diagnostics, external calibration/index use, holdout robustness, detector behavior, CNN partition variability, DiffStega reproduction, and consolidated evidence.

## Mechanical submission audit

GitHub Actions run **34708394790** (run 116), head commit `304ffe980cccd9f2217488f4836a2525bc8ba97d`, completed successfully on both jobs:
- unit tests and TOMM preflight: **PASS**;
- ACM manuscript compilation: **PASS**;
- cover-letter compilation: **PASS**;
- unresolved citation/reference guard: **PASS**;
- `Overfull \\hbox` guard: **PASS**;
- submission-PDF artifact upload: **PASS**.

Artifact `NARCIS-TOMM-submission-pdfs` has ID **10301903911**, size **600,494 bytes**, and digest `sha256:327ab7d665c5d55e39c2d310d3aa3dcfbd3f5096d181cf15efc9b7b658368a81`.

## Final audit verdict

**CLAIM / CODE / DATA = PASS.**

The enriched manuscript is aligned with the frozen code/data evidence and has passed the strengthened mechanical submission gate.