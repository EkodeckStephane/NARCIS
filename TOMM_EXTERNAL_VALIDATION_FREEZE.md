# NARCIS — External Validation Freeze

This record separates method development from external validation for the ACM TOMM revision.

## Development boundary

BOSSBase is now classified as the method-development dataset for the revised group-bank protocol. During development, multiple variants were inspected across BOSSBase partitions, including K=16 group banks, alternative group-size/reliability constructions, and the later K=8 group-bank operating point. Therefore BOSSBase cross-seed results are valuable robustness and ablation evidence, but they are not described as untouched external validation.

No Caltech-101 outcome from the final protocol defined below had been inspected when this record was frozen. Caltech-101 is the external validation dataset.

## Final protocol frozen before Caltech-101 outcomes

The following choices are fixed for every Caltech-101 partition and may not be changed in response to its results:

- codebook size: `K=8`;
- codebook family: one-dimensional balanced quantile codebook;
- projection candidates: first 16 clean-descriptor principal directions plus 32 deterministic random directions;
- calibration attack set: JPEG 80/50, Gaussian 5/12, blur 0.8/1.5, resize 0.75/0.50, crop 0.05/0.10, rotation 3/7 degrees;
- group size: `5` covers per coded symbol;
- group decoding: strict majority label;
- Reed–Solomon parity: `128` bytes;
- plaintext lengths: `8`, `32`, and `64` bytes;
- messages: 10 per plaintext length, 30 authenticated sessions total;
- authenticated sequences: globally unique `0..29` over the complete workload;
- mapping: balanced cyclic keyed Gray mapping from `TOMM_BALANCED_SESSION_MAPPING_FREEZE.md`;
- one deterministic benchmark master key per dataset partition, reused across the 30 benchmark messages with unique 96-bit AES-GCM nonces; deterministic key generation is for reproducibility only and is not production key-management guidance;
- cover-selection context: HMAC-derived from the selection subkey, authenticated sequence, protected payload, codebook label, group signature, and group membership identifiers;
- no cover is reused within one transmission;
- groups may be reused across different authenticated sessions because the keyed context changes.

## Projection selection criterion

Projection choice uses clean embeddings and the twelve calibration attacks only. For each candidate direction:

1. fit the K=8 quantile codebook on clean index embeddings;
2. compute per-cover correctness under all twelve calibration attacks;
3. compute, for every codebook label and attack, the analytical lower bound on the number of unavoidable majority-failing groups of five;
4. rank compatible candidates lexicographically by:
   - minimum maximum unavoidable bad-group fraction;
   - minimum summed unavoidable bad-group fraction;
   - maximum number of fully stable covers;
   - minimum post-IPW maximum absolute standardized mean difference;
   - minimum post-IPW mean absolute standardized mean difference;
   - deterministic direction name.

No holdout attack, steganalyzer score, payload recovery result, or Caltech category label participates in projection choice.

## Group-bank construction

Within each clean codebook label, all covers are partitioned exactly once into groups of five. The construction minimizes majority-failing group/attack cells and compares the obtained count with the analytical lower bound. The group bank uses calibration correctness only.

During emission, groups are partitioned by their calibration majority-failure signature. The requested prefix is scheduled to track the natural signature proportions of the complete label-specific group bank, with HMAC ranking used only as the deterministic secret-dependent tie-break/order within each signature.

This signature balancing is part of the frozen method and does not use detector outputs.

## Evaluation outputs

For every Caltech-101 seed `11, 29, 47, 71, 101`, report without partition-specific repair:

- projection selected by the frozen calibration criterion;
- group-bank lower-bound diagnostics;
- feasibility for every 8/32/64-byte message;
- authenticated plaintext recovery over all calibration and holdout attacks;
- symbol accuracy and Reed–Solomon corrections;
- unique-cover ratio and cover-frequency concentration;
- session-level global-statistics, residual/SRM-lite, GLCM, and CNN detectability with repeated splits/initializations;
- uncertainty intervals across sessions and partitions.

Any failure remains in the record. Caltech-101 results are not used to redesign K, group size, parity, projection ranking, group-bank objective, mapping, or detector protocol.
