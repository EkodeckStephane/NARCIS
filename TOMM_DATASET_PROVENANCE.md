# NARCIS — TOMM Dataset Provenance

This file records the dataset assets used for the fresh ACM TOMM retraining and validation campaign. The datasets are kept outside Git because their redistribution terms and sizes make repository inclusion inappropriate.

## BOSSBase 1.01

Verified local corpus:

- images: **10,000**;
- format: PGM;
- image mode: grayscale (`L`);
- dimensions: **10,000/10,000 at 512 × 512**;
- unreadable/corrupted images: **0**.

The uploaded multipart archive (`BOSSbase.z01` … `BOSSbase.z05` + `BOSSbase.zip`) was merged into a standard ZIP and passed `unzip -t` with no compressed-data errors.

Merged archive SHA-256:

`396be6f36f8c183312d7223b745fcffb5748606c3c8ec79579f7c5703143e9b4`

Per-file manifest SHA-256:

`c6c23fa3a8cb812e41b5f6bf9dd1462f02ec20513dfdd4837c11babe1c063b20`

## Caltech-101

Verified local corpus extracted from `101_ObjectCategories.tar.gz`:

- images: **9,144**;
- directories/classes: **102** (101 object categories plus `BACKGROUND_Google`);
- source image modes: **8,733 RGB + 411 grayscale**;
- variable native dimensions;
- unreadable/corrupted images: **0**.

The NARCIS cross-dataset loader converts every source image to RGB before centre-fitting to the declared channel size, so the experimental tensor input remains uniformly RGB. The source corpus itself must therefore not be described as containing 9,144 natively RGB images.

Uploaded wrapper archive SHA-256:

`331234750fc7f77520e50d9565e8b6907b03565e30320da1401130db08c61f91`

Per-file manifest SHA-256:

`d0405bbe0bbd320a547e67309799a54db58ca2bb0bd48d0352fe54ba91c5f724`

## Integrity procedure

For every discovered image, the TOMM preparation pass:

1. opened and fully decoded the image with Pillow;
2. recorded relative path, byte size, SHA-256, dimensions, mode, and Caltech category where applicable;
3. rejected unreadable files;
4. generated immutable CSV manifests whose aggregate SHA-256 values are listed above.

The complete manifests remain experimental artifacts and are not required to redistribute the copyrighted/public datasets themselves.

## Fresh-training status

The historical `encoder_seed_*.pt` files were not available in the persistent workspace. The TOMM campaign therefore performs a fresh training run using the frozen seeds `11, 29, 47, 71, 101`. Historical consolidated results remain comparison evidence only; the TOMM manuscript will use new numerical results only after the fresh run and claim/data audit are complete.
