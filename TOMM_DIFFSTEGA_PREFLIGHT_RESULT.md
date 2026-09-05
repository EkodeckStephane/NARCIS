# NARCIS — DiffStega frozen preflight result

This record captures the external baseline preflight performed before any DiffStega outcome is inspected.

## Run identity

- NARCIS branch: `tomm-revision`
- GitHub Actions run: `33991805600`
- Upstream DiffStega commit: `73cd7cb8d102f4fc0f5bb168a71cfb948077d89a`
- Upstream tracked changes: none
- Python: `3.11.5`

## Frozen package checks

All frozen release versions matched after normalizing the official PyTorch local wheel build tag (`+cpu` in the hosted CPU preflight; the faithful GPU run will use the CUDA 12.1 build):

- torch 2.1.0
- torchvision 0.16.0
- torchaudio 2.1.0
- diffusers 0.26.3
- accelerate 0.23.0
- transformers 4.38.2
- controlnet-aux 0.0.7

## Model repositories resolved

- `h94/IP-Adapter`: revision `018e402774aeeddd60609b4ecdb7e298259dc729`, public, non-gated
- `runwayml/stable-diffusion-v1-5`: revision `451f4fe16113bff5a5d2269ed5ad43b0592e9a14`, public, non-gated
- `GraydientPlatformAPI/picx-real`: revision `5cac84cdb359689917d61a2e76ef3859483aebca`, public, non-gated

## Required discrete asset hashes

- `ip-adapter-plus_sd15.bin`: `1cb77fc0613369b66be1531cc452b823a4af7d87ee56956000a69fc39e3817ba`
- `ip-adapter-plus-face_sd15.bin`: `aa09c22b49ef63474dcde12f26a35b8b8e9b755b716a553aa29e8dbe8d21e0c9`
- IP-Adapter image encoder `pytorch_model.bin`: `3d3ec1e66737f77a4f3bc2df3c52eacefc69ce7825e2784183b1d4e9877d9193`
- IP-Adapter image encoder `config.json`: `625d37b31afbf2f0792a87846b3654ee23f20568409e35b78a1f795b04e1a7a1`

## Official UniStega corpus

Official Google Drive archive SHA-256:

`768aaf95f8c7d06c5f568c79bebdbaaa4b8a7ab59c1a023a2f83a0c076f89096`

The official archive stores the three prompt directories directly at archive root. A filesystem alias `dataset/UniStega -> .` is therefore used only to satisfy the unchanged upstream README command paths; no corpus file is moved, renamed, filtered, or edited.

Verified counts and config hashes:

- content: 42 images; config SHA-256 `89ba723615a0911e220579b874bdf29607fc7fa32a43c1a546d1f81de2a33dc5`
- similar: 30 images; config SHA-256 `6377a5e0c037d6d000fe7c0e6dec0fda3d289971596b0b1e6e3fa032c1cc2a1d`
- style: 28 images; config SHA-256 `814b7ac6418160c9451a5fab1ec863222ffdc6714e44b2616718cf8d8680453d`
- total: 100 images

## Gate result

PASS:

- exact upstream commit
- unchanged tracked upstream source
- exact Python 3.11.5
- frozen package release versions
- required IP-Adapter assets
- complete UniStega corpus and configs

EXPECTED HOSTED-RUNNER BLOCKER:

- `cuda_available = false`

Therefore GitHub Actions is suitable for provenance/preflight but cannot be used to label the DiffStega reproduction as executed. The next execution must run the frozen commands on an NVIDIA GPU runtime. The repository provides `tools/bootstrap_diffstega_free_gpu.sh` and `notebooks/TOMM_DiffStega_Free_GPU.ipynb` for that purpose.
