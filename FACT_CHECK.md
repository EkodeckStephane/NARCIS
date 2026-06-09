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
| Both detector confidence intervals include 0.5 | `campaign_report.json` | Verified |
| Qualification ablation falls to 43.65% message success | Secondary CIFAR-100 campaign | Verified for that controlled campaign |

## Bounded Claims

- The detector results apply only to the two implemented detector classes.
- The results do not establish universal undetectability.
- The 3--4 bits/cover values are finite-index operating points, not global
  capacity records.
- Comparisons with published systems use reported context because datasets,
  attacks, and protocol overheads differ.
- Cross-dataset validation and end-to-end SRNet evaluation remain future work.
