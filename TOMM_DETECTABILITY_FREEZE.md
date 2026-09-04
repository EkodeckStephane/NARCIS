# NARCIS — Final Traffic Detectability Freeze

This record freezes the complete detector battery for the final K=8, group-size-5 TOMM protocol before the residual/GLCM/CNN outcomes are inspected.

## Why the detector target changes

The final diversified group-bank scheduler uses every Caltech-101 index cover at least once across the frozen 30-session workload. Consequently, a classifier contrasting the union of transmitted covers with a set of never-transmitted covers is undefined: the latter set is empty.

The final threat model therefore tests the distribution that an observer actually sees in traffic. A transmitted cover occurrence is sampled according to its empirical transmission frequency over the 30 authenticated 8/32/64-byte sessions, while the null class is sampled uniformly from the complete frozen index. Within each repetition, the two image sets are kept disjoint so that the same image cannot appear with opposite labels in one train/test experiment.

## Frozen sampling and splits

For each Caltech-101 seed `s`:

- compute each cover's transmission frequency from the 30 frozen sessions;
- repeat 20 times with split/sampling seed `s*10000 + repeat`;
- sample 500 positive images without replacement using normalized transmission frequency as sampling probability;
- sample 500 negative images uniformly without replacement from the remaining index covers;
- stratified train/test split: 65%/35%, using the same repetition seed;
- report ROC AUC for every repetition.

This procedure does not use attack holdout outcomes or detector AUCs to change the scheduler, projection, codebook, group bank, Reed–Solomon setting, or payload protocol.

## Frozen detector battery

1. **Global statistics logistic regression**: mean, standard deviation, horizontal and vertical absolute-gradient means, 32-bin entropy, and 0.1/0.9 intensity quantiles.
2. **SRM-lite residual ExtraTrees**: the four versioned residual kernels, 9-bin clipped residual histograms plus residual mean, standard deviation, mean absolute value, and 0.9 absolute quantile; ExtraTrees with 300 trees, `max_features="sqrt"`, balanced class weights.
3. **GLCM logistic regression**: the versioned 5-dimensional four-direction GLCM texture representation; StandardScaler plus balanced logistic regression.
4. **Selection CNN**: the versioned 16/32/64-channel lightweight CNN, AdamW `lr=1e-3`, `weight_decay=1e-4`, batch size 32, 8 epochs.

## Uncertainty

For each detector and partition, report the mean AUC and a deterministic percentile bootstrap 95% interval of the 20 repetition-level AUCs using 10,000 bootstrap resamples and seed `20260904 + s`. Also report the pooled five-partition mean and a partition-level interval without treating repeated splits as independent datasets.

## Interpretation

AUC estimates are reported as detectability measurements, not as formal evidence of indistinguishability. Any reproducible above-chance signal remains in the TOMM record. No detector result is used for method retuning after this freeze.
