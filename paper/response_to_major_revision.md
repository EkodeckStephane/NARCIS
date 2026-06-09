# Response to the major-revision assessment

## Summary

The manuscript now reports principal BOSSBase and cross-dataset Caltech-101
evaluations. The earlier CIFAR-100 study is retained only as a controlled
ablation and local descriptor comparison.

## Critical points

1. **High-resolution evaluation**

   Added BOSSBase 1.01: 10,000 grayscale photographs at native 512 x 512
   resolution. Channel attacks are applied at native resolution; encoder input
   is then resized to 128 x 128. Five deterministic partitions were evaluated.

2. **Full-paper extension**

   The related-work section now contains 30 cited references. A detailed TikZ
   encoder figure, convergence curves, sensitivity analysis, computational
   measurements, two selection detectors, and an expanded security discussion
   were added. The compiled Elsevier double-column manuscript is nine pages,
   which corresponds to a substantially longer single-column manuscript.

3. **Pagination**

   Multi-pass compilation and float barriers corrected the stale page count.
   The final PDF reports `Page 9 of 9`.

## Important points

4. **Hyperparameters and training**

   Training was extended from two to five epochs. Complete loss curves are
   reported for five seeds. A targeted study compares dimensions 32, 64, and
   128; weights 25/25/1, 1/1/1, and 25/10/1; and PC1, PC2, PC3, and a fixed
   random projection. The text explicitly states that PC1 is deterministic and
   variance-maximising, not stability-optimal.

5. **Stronger detectability analysis**

   Added a non-linear ExtraTrees detector using 52 high-pass residual
   co-occurrence summaries and a learned three-stage selection CNN alongside
   the seven-feature logistic detector. The three detectors are evaluated on
   both BOSSBase and Caltech-101. The manuscript reports the small classical
   detector shift on Caltech-101 rather than inferring universal
   undetectability.

6. **Statistical scope**

   The principal campaign now uses five seeds and ten messages per seed:
   1,050 end-to-end message-condition trials. All 1,050 were recovered.

7. **Keyed Gray permutation**

   The mapping is now specified by an explicit HMAC-derived shift,
   orientation, Gray transform, forward permutation, and inverse table.

## Principal results

- Complete-message recovery: 1,050/1,050.
- Mean symbol accuracy: 98.74%.
- Worst individual symbol accuracy: 81.61%.
- Feasible capacity: 4 bits/cover on four partitions and 3 bits/cover on one.
- Net plaintext rate: 0.184 or 0.138 bits/cover for eight-byte messages.
- Maximum Reed-Solomon corrections: 61 byte positions.
- Global logistic AUC: 0.518, 95% CI [0.489, 0.547].
- Residual ExtraTrees AUC: 0.514, 95% CI [0.486, 0.543].

## Additional cross-dataset revision

Caltech-101 adds 9,144 variable-resolution RGB natural images. Five
deterministic train/index partitions produce 525 further message-condition
trials, all recovered. Every partition supports 4 bits per cover. The combined
evidence is 1,575/1,575 authenticated recoveries.

## Residual limitations

The evidence remains bounded to the declared attacks, two image corpora, and
three targeted selection detectors. A faithful executable comparison with a
recent complete coverless protocol and traffic-level sequence analysis would
further reduce reviewer risk.
