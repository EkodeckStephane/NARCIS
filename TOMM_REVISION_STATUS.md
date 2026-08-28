# NARCIS — ACM TOMM Revision Status

## Target

Primary target: **ACM Transactions on Multimedia Computing, Communications, and Applications (TOMM)**.

Canonical working title:

> NARCIS: Authenticated Neural Coverless Image Signaling with Attack-Qualified Codebooks and Error Correction

The title is frozen across manuscript and submission assets until a scientifically motivated title revision is made once and propagated everywhere.

## Scientific revision rule

No previously reported adverse result is removed by wording alone. A conclusion changes only if a preregistered/reproducible method change and a fresh experiment support the change. Historical results remain preserved on `main`; all TOMM work is isolated on `tomm-revision`.

## Verified weaknesses inherited from the previous manuscript

1. Caltech-101 seed 47 showed a weak but reproducible selection signal in the repeated CNN detector (historical mean AUC 0.533; historical 95% interval [0.517, 0.548]).
2. The projection search on BOSSBase seed 11 improved the minimum stable bucket but did not support the prior high-variance-instability explanation.
3. Payload scalability for 32/128 bytes was previously evaluated at protocol/framing level; the TOMM revision requires real image-channel end-to-end trials for 32 and 64 bytes.
4. Published-state-of-the-art superiority was not established by the prior local DCT/histogram baselines.

## Method corrections already implemented on this branch

### A. Payload-dependent diversified cover selection

`NarcisProtocol.encode()` no longer restarts from the same first cover in every bucket for every protected payload. Candidate covers are now ranked by a deterministic HMAC-derived exponential race. The ranking is:

- deterministic for the same protected payload and key;
- different for different protected payloads;
- without replacement within a transmission;
- compatible with per-cover distribution-balancing weights.

This removes a protocol-level concentration mechanism that could itself create a detectable transmitted-cover subset.

### B. Distribution-preserving qualification weights

The previous inverse-odds weight `(1-p)/p` has been replaced, for the TOMM validation path, by stabilized inverse-probability weights proportional to `P(S=1)/P(S=1|X)`, where `S` denotes attack stability. Diagnostics now report effective sample size and standardized mean differences before/after weighting.

### C. GLCM cover-selection threat

A four-direction GLCM texture implementation has been added using Energy, Contrast, Entropy, Correlation, and the published Cao–Wang–Zhang complexity combination

`T = 7/60 E + 11/20 C + 1/5 Ent + 2/15 Cor`.

Reference: H. Cao, Z. Wang, and X. Zhang, “On improving steganalysis against cover selection steganography,” *Cybersecurity*, vol. 8, art. 115, 2025. DOI: 10.1186/s42400-025-00423-z.

### D. Calibration-locked TOMM validation path

A dedicated TOMM runner now freezes the projection search to calibration data, applies the revised selection mechanism, executes real 8/32/64-byte image-channel transmissions, and evaluates global, residual, CNN, and GLCM selection detectors. The default evaluation uses the five previously defined seeds `11, 29, 47, 71, 101`.

## TOMM positioning references verified for integration

The revision will position NARCIS against work published in the target journal where scientifically relevant, including:

- Z. Zhou et al., “Progressive Generative Steganography via High-Resolution Image Generation for Covert Communication,” *ACM TOMM*, 21(10), Article 296, 2025. DOI: 10.1145/3760531.
- H. Li et al., “A Siamese Inverted Residuals Network Image Steganalysis Scheme based on Deep Learning,” *ACM TOMM*, 19(6), Article 214, 2023. DOI: 10.1145/3579166.
- P. Neekhara et al., “FaceSigns: Semi-fragile Watermarks for Media Authentication,” *ACM TOMM*, 20(11), Article 337, 2024. DOI: 10.1145/3640466.
- Y. Sun, J. Liu, and R. Zhang, “Generative Image Steganography Based on Guidance Feature Distribution,” *ACM TOMM*, 20(11), 2024. DOI: 10.1145/3625297.
- D. Wang, G. Yang, Z. Guo, and J. Chen, “Enhancing Adversarial Embedding based Image Steganography via Clustering Modification Directions,” *ACM TOMM*, 20(1), 2024. DOI: 10.1145/3603377.

These citations must support explicit scientific comparisons; they are not journal-target citation padding.

## External baselines selected for comparison

### Executable peer-reviewed baseline: DiffStega

The primary executable external baseline is Y. Yang et al., “DiffStega: Towards Universal Training-Free Coverless Image Steganography with Diffusion Models,” *IJCAI 2024*, pp. 1579–1587, DOI 10.24963/ijcai.2024/175.

Official repository: `evtricks/DiffStega`.

Frozen upstream reference commit: `73cd7cb8d102f4fc0f5bb168a71cfb948077d89a`.

GitHub reports no repository license metadata. Therefore its source is **not copied into NARCIS**. It will be executed as an external dependency in a separate environment, with package/model identifiers and deviations recorded. Direct comparison is limited to genuinely common metrics; generative reconstruction quality is not treated as equivalent to NARCIS finite-index plaintext capacity.

### Closest conceptual comparator: Guo–Ping 2026

The 2026 Guo–Ping stability-aware PZM/SA-PQE method remains the closest conceptual comparator. No verified official public implementation has been located. Its published values may be used as clearly labeled literature results under its original datasets and attacks, but it must not be described as reimplemented until a faithful implementation is independently validated.

The detailed comparison policy is frozen in `TOMM_BASELINE_PROTOCOL.md`.

## Fresh experiment gates

The TOMM manuscript must not replace historical numbers until all applicable gates pass.

### Gate T1 — selection balance

For every evaluated partition, report distribution-balance diagnostics for the attack-stable pool and transmitted subset. The main target is that the revised mechanism does not create a reproducible detector advantage over chance under the declared detector battery.

### Gate T2 — projection generalization

Run calibration-locked projection selection independently on all predefined BOSSBase and Caltech-101 partitions. Candidate choice uses calibration information only. Holdout transformations remain untouched until final evaluation.

### Gate T3 — real payload channel

Run actual end-to-end image transmissions for at least 8, 32, and 64 plaintext bytes, through all declared calibration/holdout channel transformations. Report covers required, symbol accuracy, authenticated message recovery, and RS corrections.

### Gate T4 — attack battery

Evaluate at least global statistics, residual-feature classifier, CNN selection detector, and the GLCM texture detector. Detector repetitions/splits and confidence intervals must be frozen before inspecting final holdout conclusions.

### Gate T5 — recent comparison

Run DiffStega from its frozen upstream reference in a documented environment and separate directly comparable metrics from protocol-family differences. Guo–Ping 2026 remains a literature-level comparator unless a faithful implementation becomes available. Do not claim superiority where protocols/datasets do not permit a matched comparison.

### Gate T6 — claim/code/data audit

Every number entering abstract, tables, figures, highlights, and cover letter must be generated from versioned result files and traced to a command/configuration. No manuscript-only result is allowed.

## Reproducibility blocker currently verified

The GitHub repository contains consolidated CSV/JSON results but does **not** contain the trained `encoder_seed_*.pt` checkpoints or the BOSSBase/Caltech-101 datasets. Consequently, the new full campaigns cannot be truthfully reported as executed from the connected repository alone. The code changes can be reviewed and unit-tested independently, but fresh scientific results require the original local checkpoints or retraining with the datasets.

Until those experiments run, the old manuscript's numerical conclusions remain historical evidence only and the TOMM abstract/results must not be rewritten to imply improved detectability.
