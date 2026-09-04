# NARCIS — TOMM Scientific Closure Record

## Scope of this closure

This record closes the present TOMM revision campaign as an audited scientific state. It freezes what is supported by persisted evidence and separates it from work that was planned but not completed. The purpose is to prevent later manuscript text, cover letters, or repository documentation from overstating the validation level.

Canonical title:

> NARCIS: Authenticated Neural Coverless Image Signaling with Attack-Qualified Codebooks and Error Correction

Target considered during this campaign: ACM Transactions on Multimedia Computing, Communications and Applications (TOMM).

## Method state frozen at closure

The revision introduced and audited the following substantive changes:

- payload- and session-dependent cover diversification;
- stabilized inverse-probability weighting for selection-balance control;
- GLCM texture diagnostics inspired by Cao–Wang–Zhang;
- K=8 balanced quantile codebooks for the final group-bank operating point;
- complementary groups of five covers with strict majority decoding;
- Reed–Solomon parity of 128 bytes;
- authenticated 30-session workloads spanning 8, 32, and 64 plaintext bytes;
- globally unique authenticated sequences 0..29;
- exact balanced cyclic keyed Gray cluster mapping with a fixed secret orientation;
- reproducible benchmark key/nonce derivation and a versioned cached-validation path.

BOSSBase served as the method-development dataset because K, grouping, and related operating choices were inspected during development on that dataset. Caltech-101 was then used as the external calibration dataset under the frozen protocol.

## Persisted BOSSBase development evidence

The corrected K=8/group-size-5/RS128 development campaign completed all five predefined seeds. Across the 12 calibration attacks it produced 1,800/1,800 authenticated recoveries. Session-level mean AUCs across seeds were approximately 0.5139 for the seven global statistics and 0.5184 for the clean-15D representation. The largest Reed–Solomon correction count in the calibration campaign was 7.

BOSSBase holdout evidence was additionally completed for at least seeds 11, 29, and 47 in the execution record, with authenticated recovery preserved under the evaluated holdout attacks despite stronger crop/rotation degradation. These holdout observations remain development evidence and are not used as external validation claims.

## Persisted Caltech-101 external calibration evidence

All five predefined Caltech-101 seeds completed the frozen external calibration protocol. The persisted aggregate is `tomm_results/caltech_external_calibration_aggregate.json`.

| Seed | Projection | Stable covers | Stable fraction | Authenticated recovery | Max RS corrections | Global7 AUC | Clean15 AUC |
|---:|---|---:|---:|---:|---:|---:|---:|
| 11 | random_04 | 4,184 | 0.5977 | 360/360 | 5 | 0.5176 | 0.5254 |
| 29 | random_04 | 3,795 | 0.5421 | 360/360 | 37 | 0.5138 | 0.5274 |
| 47 | random_15 | 4,756 | 0.6794 | 360/360 | 0 | 0.5119 | 0.5184 |
| 71 | random_20 | 3,933 | 0.5619 | 360/360 | 11 | 0.5172 | 0.5195 |
| 101 | random_28 | 4,167 | 0.5953 | 360/360 | 0 | 0.5112 | 0.5266 |

Aggregate external-calibration result:

- 1,800/1,800 authenticated recoveries;
- success rate 1.000;
- maximum observed RS corrections: 37;
- mean Global7 session AUC across seeds: 0.51435 (seed-level SD 0.00295);
- mean Clean15 session AUC across seeds: 0.52346 (seed-level SD 0.00418);
- mean stable-cover fraction: 0.59529, range 0.54214–0.67943;
- all 7,000 covers were used in every seed.

These numbers support the statement that the revised group-bank protocol generalized across the five Caltech-101 partitions under the declared calibration attack set while preserving authenticated message recovery and keeping the two evaluated session-level detectors near chance.

## Gates not completed

The following planned TOMM gates do not have a complete persisted evidence set in the workspace at closure:

1. Caltech-101 holdout transformations for all five seeds under the final frozen protocol;
2. the full repeated detector battery on the final external campaign, including residual/SRM-lite, GLCM, and CNN with confidence intervals;
3. a fully matched external DiffStega execution under a documented comparable protocol;
4. the final manuscript-wide claim/code/data audit after insertion of the fresh results.

No manuscript, abstract, conclusion, highlight, or cover letter may imply that these gates passed.

## Scientific interpretation

The revision resolved the most serious method-level defect exposed by the previous submission cycle: concentrated and distribution-shifted cover selection. The resulting group-bank construction produced perfect authenticated recovery over the frozen calibration battery on both development and external Caltech partitions, while the evaluated global and clean-descriptor detectors remained close to chance.

However, external holdout robustness and the full modern selection-detection battery are still missing. Therefore the present evidence supports a strong revised proof of concept and a credible external calibration generalization result, but not the stronger statement that NARCIS has completed a journal-grade adversarial generalization and detectability evaluation.

## Submission decision at closure

**Do not release the present manuscript for TOMM submission as a complete final article.**

Reason: submitting now would require either omitting the unfinished gates or weakening the claims substantially. Given the previous prescreen rejection for novelty/technical depth/presentation and the user's explicit requirement to avoid unsupported claims, the scientifically defensible closure is to archive the current revision rather than force a third submission with incomplete external holdout/detector evidence.

If the work is reopened later, the continuation point is explicit and limited: run Caltech holdouts for all five seeds, run the repeated SRM-lite/GLCM/CNN detector battery, execute the frozen DiffStega comparator where metrics are genuinely common, then perform one final claim/code/data audit. No redesign of K, group size, mapping, or calibration selector should be made in response to those external results.

## Archival rule

Historical and adverse results remain preserved. The main branch continues to represent the historical manuscript state; `tomm-revision` records the audited revision path. This closure does not erase the previous Caltech detector signal or exploratory variants. It records that the revised protocol substantially improved the calibration evidence while leaving specific final gates incomplete.
