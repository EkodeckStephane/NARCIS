# NARCIS — TOMM Baseline Comparison Protocol

## Purpose

This document freezes how recent external methods will be compared with NARCIS before final TOMM results are inspected. Its purpose is to prevent metric shopping and misleading cross-family claims.

## Comparator A — DiffStega (executable, peer reviewed)

Publication:

Y. Yang, Z. Liu, J. Jia, Z. Gao, Y. Li, W. Sun, X. Liu, and G. Zhai, “DiffStega: Towards Universal Training-Free Coverless Image Steganography with Diffusion Models,” *Proceedings of IJCAI 2024*, pp. 1579–1587. DOI: 10.24963/ijcai.2024/175.

Official implementation:

- repository: `evtricks/DiffStega`
- frozen reference commit: `73cd7cb8d102f4fc0f5bb168a71cfb948077d89a`
- upstream license metadata: none reported by GitHub as of the protocol freeze

Accordingly, upstream source code is not copied into NARCIS. Reproduction is performed in a separate environment against the frozen external repository.

### Environment to reproduce

The upstream README specifies Python 3.11.5, PyTorch 2.1.0, torchvision 0.16.0, CUDA 12.1/12.2-class environment, Diffusers 0.26.3, Accelerate 0.23.0, Transformers 4.38.2, and ControlNet Auxiliary 0.0.7, plus IP-Adapter pretrained weights. Exact installed versions and model identifiers/hashes must be recorded in the benchmark manifest.

### Metrics permitted for direct comparison

Because DiffStega and NARCIS solve different coverless communication formulations, only metrics with a genuinely common interpretation may appear in a direct numerical table:

1. **Recovery success under the same post-generation/channel transformations**, where both systems expose a recoverable information object under that transformation.
2. **Wall-clock encode/decode cost**, with hardware reported separately and without claiming hardware-normalized superiority unless the hardware is matched.
3. **Output-image detectability under a common detector**, only if positive/negative classes and sampling protocol are defined equivalently.
4. **Failure rate under incorrect/unauthorized secret material**, when the semantic security question is comparable.

### Metrics that must remain family-specific

The following must not be presented as directly interchangeable without an explicit derivation:

- NARCIS bits per selected natural cover vs DiffStega hidden-image/image reconstruction capacity;
- unchanged-cover selection leakage vs generated-image steganalysis;
- finite-index bucket feasibility vs generative sampling feasibility;
- NARCIS authenticated plaintext recovery vs perceptual reconstruction quality (PSNR/SSIM/LPIPS).

These are reported side-by-side under separate metric definitions, not ranked as if they were the same quantity.

## Comparator B — Guo–Ping 2026 (closest conceptual comparator)

Publication:

B. Guo and P. Ping, “Towards robust and high-capacity coverless image steganography,” *Knowledge-Based Systems*, vol. 338, 115472, 2026. DOI: 10.1016/j.knosys.2026.115472.

Role:

This is the closest high-priority literature comparator because it combines stable visual descriptors, stability-aware quantization, and representative selection. Published values may be cited as **reported literature results** with their original datasets and attack protocol.

A matched reimplementation must not be claimed unless all algorithmic details required to reproduce PZM extraction, SA-PQE, stability regularization, clustering/representative selection, payload mapping, and attack protocol are implemented and independently validated. No verified official public implementation has been located at protocol freeze.

## Comparator C — recent robustness context

Recent deep-hashing / restoration-based coverless methods can be included as literature context when verified bibliographic data and original protocol definitions are available. Their reported values remain labeled “reported by authors” unless rerun.

## NARCIS comparison conditions

### Datasets

Primary NARCIS validation remains on the frozen BOSSBase and Caltech-101 partitions already used by the project. A new comparator dataset is introduced only when required to run an external method faithfully; conclusions are then dataset-scoped.

### Channel transformations

For a matched NARCIS comparison, every method must be evaluated under the exact transformation parameters applied to its output image whenever the method permits that transformation. No method receives an easier transformation under the same table column.

### Randomness

- NARCIS: frozen seeds `11, 29, 47, 71, 101`.
- detector repetitions: 20 unless resource constraints require a preregistered change before results are inspected.
- external methods: preserve their native seeds where required and add repeated independent seeds when supported.

### Statistical reporting

Report mean, dispersion/95% confidence interval where meaningful, and sample count. A single best run is never used as the headline comparison.

### Claim policy

Use “outperforms” only for a directly matched metric with appropriate uncertainty and protocol equivalence. Otherwise use formulations such as “reports,” “achieves under its original protocol,” or “addresses a different operating regime.”

## Execution gate

No comparative table enters the TOMM manuscript until the benchmark manifest records:

- exact upstream commit or release;
- environment/package versions;
- pretrained model identifiers;
- dataset/sample list or hashes;
- commands;
- raw outputs;
- metric extraction script;
- any incompatibility or deviation from the original method.
