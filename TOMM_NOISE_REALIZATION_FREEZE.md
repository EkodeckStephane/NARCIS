# NARCIS — Gaussian Channel Realization Freeze

## Reproducibility issue addressed

The historical `attack_suite()` Gaussian closures maintain mutable RNG state. If the same closure is called after a different number or ordering of images, the concrete noise realization changes even when the nominal seed is unchanged.

The TOMM campaign therefore treats Gaussian channel realizations as explicit versioned experimental assets rather than implicit call-history state.

## Canonical image order

For every partition, the index list is generated from the sorted dataset paths and the frozen partition permutation. A canonical dataset-relative identifier is stored for each image. Gaussian arrays are generated over this complete frozen index order.

## Projection-calibration realization

The projection-selection cache uses one complete-index realization for each calibration noise level:

- `gaussian_5_projection`: base partition seed + 1;
- `gaussian_12_projection`: base partition seed + 2.

These arrays may be used by the calibration-locked projection rule only.

## Independent end-to-end realization

End-to-end payload validation at the same nominal calibration noise levels uses independent complete-index realizations:

- `gaussian_5_evaluation`: base partition seed + 1001;
- `gaussian_12_evaluation`: base partition seed + 1002.

Thus successful payload recovery at sigma 5/12 is not evaluated on the exact random perturbations that participated in projection selection.

## Holdout realizations

Holdout Gaussian levels remain excluded from projection/coding tuning and use independent seeds:

- `gaussian_9_holdout`: base partition seed + 2003;
- `gaussian_15_holdout`: base partition seed + 2004.

## Cache equivalence

Each Gaussian realization is applied once to every image in the canonical complete-index order and its encoder embedding is cached. Later payload simulations select rows from this cache. This is exactly equivalent to applying that frozen realization first and then selecting the corresponding transformed images; it is not an analytical approximation.

No detector output or holdout success result determines these seeds.
