# NARCIS — Final Multi-Session Detector Audit Freeze

This record freezes the final complementary detector audit before its results are inspected. It does not modify NARCIS, the K=8 codebook, projection choices, group banks, FEC, mapping, payloads, or any transmitted-cover schedule.

## Why the legacy union detector is undefined for the final protocol

The revised payload-dependent group-bank scheduler deliberately diversifies traffic across authenticated sessions. Over the frozen 30-session 8/32/64-byte workload, every one of the 7,000 Caltech-101 index covers is used at least once in every partition. Consequently, a detector defined as `union(transmitted covers) versus never transmitted covers` has no negative class and cannot be evaluated.

The already frozen per-session global7 and clean15 detectors remain valid and are retained unchanged. The residual, GLCM, and CNN audit below operationalizes the same cover-selection threat without collapsing the 30 sessions into a degenerate union.

## Frozen multi-session threat model

For each Caltech-101 partition independently, construct a binary target matrix `Y` of shape `7000 x 30`, where `Y[i,q]=1` exactly when cover `i` is transmitted in authenticated session `q`. The detector receives only the natural cover image (or fixed image-derived features) and has one output per frozen session. Session identity is therefore represented only by the output head; the detector never receives payload bytes, cryptographic material, attack labels, codebook labels, or group-bank metadata.

All train/test splits are **image-disjoint**: a cover image and all of its 30 session labels belong entirely to either train or test. This prevents image identity leakage between train and test.

## Repetitions and split rule

- seeds: `11, 29, 47, 71, 101`;
- detector repetitions per partition: `20`;
- split seed for repeat `r`: `partition_seed * 10000 + r`;
- test fraction: `0.35`;
- all 7,000 index covers are eligible; no detector-dependent sampling or tuning is allowed;
- AUC is computed independently for each of the 30 session heads on the test images, then macro-averaged across heads; per-head AUCs are retained.

## Frozen detectors

### SRM-lite / residual ExtraTrees

Use the existing 52 residual features implemented in `run_bossbase_campaign.py`: four fixed high-pass kernels, nine-bin clipped residual histograms and four residual moments per kernel. Fit one `ExtraTreesClassifier` in native multi-output mode with:

- `n_estimators=300`;
- `max_features="sqrt"`;
- `class_weight="balanced"`;
- `random_state=split_seed`;
- `n_jobs=-1`.

### GLCM texture detector

Use the existing five GLCM features from `src/narcis/glcm.py` (four-direction Energy, Contrast, Entropy, Correlation, plus the Cao–Wang–Zhang complexity combination). Standardize features on the training images and fit one balanced logistic-regression classifier per session head with `max_iter=2000`.

### Lightweight CNN

Use the existing SelectionCNN backbone from `run_bossbase_campaign.py`, with a 30-logit output layer instead of a single logit so that one image-disjoint training run evaluates all frozen sessions simultaneously. Images are center-fitted to the existing 256x256 Caltech channel input and bilinearly resized to 64x64 for the detector, exactly as in the legacy detector path. Training is frozen at:

- AdamW, learning rate `1e-3`, weight decay `1e-4`;
- BCE-with-logits over the 30 session heads;
- batch size `32`;
- `8` epochs;
- one model per split seed;
- no early stopping or detector-based adjustment.

This multi-head change is an evaluation adaptation required by the final protocol's all-cover traffic diversity; it is not a NARCIS method change. The single-head CNN architecture and training hyperparameters otherwise remain unchanged.

## Interpretation rule

Detector results are sensitivity evidence, not a tuning objective. Any reproducible AUC above chance remains reportable. No NARCIS parameter may be changed in response to this audit. The final manuscript must distinguish the frozen per-session global/clean detector results from this stronger multi-session residual/GLCM/CNN sensitivity audit.
