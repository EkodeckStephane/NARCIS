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

## Bounded Claims

- The detector results apply only to the three implemented detector classes.
- The results do not establish universal undetectability.
- The 3--4 bits/cover values are finite-index operating points, not global
  capacity records.
- Comparisons with published systems use reported context because datasets,
  attacks, and protocol overheads differ.
- The implemented CNN targets selection bias; it is not an SRNet
  reimplementation for pixel-embedding steganalysis.
