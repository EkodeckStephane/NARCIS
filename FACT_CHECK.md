# NARCIS Fact Check

This audit maps the principal manuscript claims to released evidence.

| Claim | Evidence | Status |
|---|---|---|
| BOSSBase contains 10,000 native 512 x 512 grayscale images | `DATASETS.md`; campaign manifest | Verified |
| Five deterministic partitions were evaluated | Seeds 11, 29, 47, 71, 101 in `campaign_report.json` | Verified |
| Ten messages and 21 conditions were evaluated per seed | 1,050 rows in `end_to_end_raw.csv` | Verified |
| All complete messages were recovered | 1,050 successes in `campaign_report.json` | Verified |
| Mean symbol accuracy is 98.74% | `campaign_report.json`: 0.9873679529 | Verified |
| Worst individual symbol accuracy is 81.61% | `campaign_report.json`: 0.8160919540 | Verified |
| Four seeds support 4 bits/cover and one supports 3 | `selected_configurations.csv` | Verified |
| Global detector mean AUC is 0.518 | `selection_detectors.csv`; consolidated report | Verified |
| Residual ExtraTrees mean AUC is 0.514 | `selection_detectors.csv`; consolidated report | Verified |
| BOSSBase selection-CNN AUC is 0.515, CI [0.463, 0.566] | `q1_extension_results/report.json` | Verified |
| Caltech-101 contains 9,144 variable-resolution RGB images | dataset manifest; `DATASETS.md` | Verified |
| Caltech-101 uses five seeds and 525 message-condition trials | `q1_extension_results/report.json` | Verified |
| All Caltech-101 plaintexts were recovered | 525/525 in `q1_extension_results/report.json` | Verified |
| Caltech-101 mean/worst symbol accuracy is 98.59%/79.89% | `q1_extension_results/report.json` | Verified |
| Every Caltech-101 partition supports 4 bits/cover | `q1_extension_results/selected_configurations.csv` | Verified |
| Caltech-101 selection-CNN AUC is 0.530, CI [0.481, 0.579] | `q1_extension_results/report.json` | Verified |
| Qualification ablation falls to 43.65% message success | Secondary CIFAR-100 campaign | Verified for that controlled campaign |
| BOSSBase seed-11 matched ablation falls to 142/210 (67.62%) without qualification | `q1_reviewer_results/boss_seed11_matched_ablation_summary.csv` | Verified |
| At K=16, net rate is 0.184, 0.646, and 1.213 bits/cover for 8, 32, and 128 plaintext bytes | `q1_reviewer_results/payload_scalability.csv` | Verified |
| Attack-aware projection increases the seed-11 minimum bucket from 92 to 161 | `q1_reviewer_results/boss_projection_analysis.json` | Verified for the targeted partition |
| Repeated Caltech seed-47 CNN AUC is 0.533, CI [0.517, 0.548] | `q1_reviewer_results/caltech_seed47_selection_report.json` | Verified for 20 repeated fits |

## Bounded Claims

- The detector results apply only to the three implemented detector classes.
- Caltech-101 seed 47 has a weak but measurable matched-index selection leak;
  the results do not establish universal undetectability.
- The 3--4 bits/cover values are finite-index operating points, not global
  capacity records.
- Comparisons with published systems use reported context because datasets,
  attacks, and protocol overheads differ.
- The implemented CNN targets selection bias; it is not an SRNet
  reimplementation for pixel-embedding steganalysis.
- The attack-aware direction result is a full-index single-partition study and
  does not replace the five-seed PC1 campaign.
