# NARCIS — Frozen DiffStega GPU Reproduction

This record freezes the executable external-comparator protocol before any new DiffStega outcome is inspected for the TOMM revision.

## Upstream identity

Comparator: **DiffStega: Towards Universal Training-Free Coverless Image Steganography with Diffusion Models**, IJCAI 2024.

Official source repository: `evtricks/DiffStega`.

Frozen upstream commit:

```text
73cd7cb8d102f4fc0f5bb168a71cfb948077d89a
```

The upstream source is not copied into NARCIS. Execution must clone or checkout that exact external commit and record the resulting Git commit in the benchmark manifest.

## Faithful execution environment

The primary reproduction follows the upstream environment rather than silently adapting the model to CPU:

- Python 3.11.5;
- PyTorch 2.1.0;
- torchvision 0.16.0;
- torchaudio 2.1.0;
- CUDA 12.1 runtime class; the upstream authors report testing with CUDA 12.2;
- diffusers 0.26.3;
- accelerate 0.23.0;
- transformers 4.38.2;
- controlnet_aux 0.0.7.

The actual CUDA runtime, GPU model, VRAM, driver, operating system, package lock, and wall-clock times must be recorded. A CPU rewrite, dtype change, reduced image size, reduced diffusion-step count, or replacement model is not labeled a faithful reproduction.

## Required pretrained assets

Use the upstream model identifiers and files without substituting detector- or outcome-selected alternatives:

- Stable Diffusion 1.5: `runwayml/stable-diffusion-v1-5`;
- default reference model: `GraydientPlatformAPI/picx-real` where the upstream command requires the second model;
- IP-Adapter repository: `h94/IP-Adapter`;
- `models/ip-adapter-plus_sd15.bin`;
- `models/ip-adapter-plus-face_sd15.bin`;
- `models/image_encoder/pytorch_model.bin`;
- `models/image_encoder/config.json`.

For every downloaded asset, retain provider repository/revision metadata and SHA-256 of the local file when the asset is a discrete file. If a model provider requires authentication or license acceptance, record that requirement rather than substituting another checkpoint.

## Evaluation corpus

Use the authors' UniStega corpus, not the three README demonstration images. The published corpus contains 100 512×512 cases divided as:

- UniStega-Content: 42 images;
- UniStega-Style: 28 images;
- UniStega-Similar: 30 images.

Use the official dataset link exposed by the upstream README and retain the downloaded archive hash plus the three YAML configuration files and ordered sample lists as evidence.

No sample is removed because of a poor output, slow execution, failed recovery, unsupported control path, or low score. Any failed case remains part of the denominator.

## Frozen upstream commands

Execute the three upstream dataset commands at the frozen commit:

```bash
python main.py --yaml_path ./dataset/UniStega/similar_prompts/config.yaml --save_path ./output/UniStega_similar --null_prompt1 --optional_control auto

python main.py --yaml_path ./dataset/UniStega/content_prompts/config.yaml --save_path ./output/UniStega_content --null_prompt1 --optional_control auto

python main.py --yaml_path ./dataset/UniStega/style_prompts/config.yaml --save_path ./output/UniStega_style --null_prompt1 --edit_strength 0.7 --single_model --rand_pw --optional_control auto
```

All upstream defaults not overridden by those commands remain unchanged, including 50 sampling steps, Noise Flip scale 0.05, default edit strength 0.6 for non-style runs, and the upstream password/reference-image logic.

## Metrics and comparison policy

First reproduce the method under its native protocol. Preserve original, encrypted, correctly recovered, no-password recovered, wrong-password recovered, correct-reference, and wrong-reference outputs whenever produced.

For the native DiffStega reproduction, report the image-quality/security metrics used by the paper where their implementation is independently verifiable: PSNR, SSIM, LPIPS, face ID cosine similarity for applicable face images, CLIP Score for target-prompt agreement, and NIQE for encrypted-image naturalness. Exact metric library/model versions must be recorded.

These values are family-specific evidence. They are not converted into NARCIS bits-per-cover, finite-index feasibility, or authenticated-plaintext success.

A direct NARCIS-vs-DiffStega numerical statement is allowed only for a metric with equivalent semantics under an explicitly matched extension. Otherwise the manuscript reports the two operating regimes side by side and labels DiffStega values as reproduced under its native UniStega protocol.

## Execution gate

The DiffStega comparator is marked **executed** only when the evidence package contains:

- exact upstream commit;
- CUDA/GPU and package manifest;
- pretrained model identifiers/revisions and hashes where applicable;
- UniStega archive/config/sample hashes;
- all three complete upstream commands;
- raw stdout/stderr logs;
- output file manifest with SHA-256;
- per-case metric table and aggregate table;
- explicit list of failed or missing outputs, if any.

Until those files exist, the TOMM manuscript must not describe DiffStega as rerun or reproduced by the NARCIS authors.
