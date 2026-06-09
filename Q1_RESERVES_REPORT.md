# Q1 Reserve Resolution Report

## M1: Effective payload rate

The implemented AES-GCM, framing, and Reed-Solomon path was measured for
8-, 32-, and 128-byte plaintexts. At `K=16`, the net rates are 0.184, 0.646,
and 1.213 bits/cover. The 128-byte case spans two RS(255,127) blocks, so the
effective parity is 256 bytes rather than 128.

Evidence: `q1_reviewer_results/payload_scalability.csv`.

## M2: Principal-corpus qualification ablation

On BOSSBase seed 11, removing qualification while holding the PC1 codebook,
messages, coding, and decoder constant reduced complete recovery from 210/210
to 142/210 (67.62%). Six crop/rotation conditions produced no successful
messages, and the 5-degree rotation produced 2/10.

Evidence: `q1_reviewer_results/boss_seed11_matched_ablation_summary.csv`.

## M3: Caltech-101 selection leakage

Twenty independent balanced subsamples, splits, and CNN initialisations on
seed 47 produced mean AUC 0.533, 95% CI [0.517, 0.548], with range
0.445-0.580. The result establishes weak matched-index selection leakage.
Low-level feature shifts are small; category-composition shifts are larger,
but the analysis does not attribute the signal to one causal feature.

Evidence: `q1_reviewer_results/caltech_seed47_selection_report.json`,
`caltech_seed47_feature_shift.csv`, and
`caltech_seed47_category_shift.csv`.

## M4: Projection choice

A calibration-only search over 16 principal and 32 deterministic random
directions selected `random_15`. On the full BOSSBase seed-11 index, it
increased the stable fraction from 35.29% to 45.55% and the minimum stable
bucket from 92 to 161. The locked direction recovered 210/210 targeted trials.
Across principal directions, explained variance and stability were positively
correlated (Spearman rho 0.640, p=0.0076), so the proposed high-variance
instability explanation is not supported.

This is a targeted single-partition validation and does not replace the
five-seed PC1 campaign.

Evidence: `q1_reviewer_results/boss_projection_analysis.json`,
`boss_projection_candidates.csv`, and
`boss_seed11_ablation_raw.csv`.
