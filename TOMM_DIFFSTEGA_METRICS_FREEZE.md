# NARCIS — Frozen independent metric protocol for reproduced DiffStega outputs

This document freezes the post-execution evaluation protocol before any reproduced DiffStega output is inspected.

The upstream IJCAI 2024 paper reports PSNR, SSIM, LPIPS, FaceNet identity cosine similarity for face images, CLIP Score for target-text agreement, and NIQE for encrypted-image naturalness. The frozen upstream repository does not contain a metric-evaluation implementation. Therefore the NARCIS reproduction uses an explicitly versioned independent implementation and reports its values as reproduced metrics, distinct from the literature values printed in the DiffStega paper.

## Evaluation unit

The official UniStega corpus has 100 cases:

- content: 42;
- style: 28;
- similar: 30.

Every configured case stays in the denominator. Missing or unreadable expected output files are recorded as failures rather than removed.

For each case, the evaluator identifies exactly one of each upstream output family:

- original: `<name>.png`;
- encrypted: `<name>_hide_pw_*.png`;
- correct-password recovery: `<name>_rec_w_*.png`;
- no-password recovery: `<name>_rec_wo_*.png` excluding filenames that also contain `_w_`;
- wrong-password recovery: `<name>_rec_wo_*_w_*.png`.

The target caption comes from the corresponding official UniStega YAML entry. A case is treated as a face case when the official configuration uses `optional_control: landmark`, matching the upstream face-control path.

## Pairwise image metrics

Images are converted to RGB and compared at their produced resolution. Any size mismatch is a hard per-case evaluation failure; the evaluator does not silently resize outputs.

### PSNR

Implementation: `skimage.metrics.peak_signal_noise_ratio`, `data_range=255`.

### SSIM

Implementation: `skimage.metrics.structural_similarity`, RGB `channel_axis=2`, `data_range=255`.

### LPIPS

Implementation: official `lpips` package, AlexNet backbone, spatially averaged LPIPS distance. Input RGB tensors are mapped to `[-1,1]` as required by LPIPS.

Frozen package: `lpips==0.1.4`.

## Face identity cosine similarity

Only cases marked `optional_control: landmark` are evaluated.

Implementation:

- `facenet-pytorch==2.5.3`;
- MTCNN face extraction, `image_size=160`, `margin=0`, `post_process=True`;
- InceptionResnetV1 pretrained on VGGFace2;
- cosine similarity between L2-normalized embeddings.

If either image has no detected face, the metric is missing for that case and `face_detection_failure=true` is recorded. Such a case is not silently replaced by a center crop.

## CLIP Score

Applied to encrypted image versus official target caption.

Implementation uses Hugging Face `CLIPModel` and `CLIPProcessor` with model identifier:

`openai/clip-vit-base-patch32`

Image and text embeddings are L2-normalized. Score is `100 * max(cosine_similarity, 0)`, which preserves the conventional CLIPScore scale used in the literature. The exact resolved Hugging Face model revision is recorded in the evaluation manifest at execution time.

## NIQE

Applied to encrypted images only.

Implementation: `pyiqa==0.1.13`, metric name `niqe`, using the package's published default NIQE parameters. The installed package version and any resolvable model/parameter asset hashes are recorded in the manifest.

## Metric directions

For encrypted versus original images, lower PSNR/SSIM/ID similarity and higher LPIPS indicate stronger visual separation, while CLIP Score measures target-caption agreement and NIQE measures naturalness independently.

For correct-password recovery versus original, higher PSNR/SSIM/ID similarity and lower LPIPS are preferred.

For no-password and wrong-password recovery versus original, the security interpretation is the reverse: lower PSNR/SSIM/ID similarity and higher LPIPS indicate weaker unauthorized recovery.

## Aggregation

The evaluator emits:

- one row per UniStega case with all available metrics and completeness flags;
- subset summaries for content/style/similar;
- a global 100-case summary;
- counts of missing outputs, unreadable outputs, and face-detection failures;
- the exact package/model/environment manifest;
- SHA-256 for all consumed output files and generated CSV/JSON evidence.

Means, sample standard deviations, medians, minima and maxima are reported for finite metric values. Metric-specific valid counts are always reported next to aggregates.

## Comparison policy

The IJCAI paper's published DiffStega values remain literature reference values. NARCIS reproduced values are not substituted into the paper's table or described as numerically identical unless the independently frozen implementation actually reproduces them within a stated tolerance.

No metric choice, backbone, face subset, failed-case rule, or aggregation rule is changed after inspecting reproduced DiffStega outcomes.
