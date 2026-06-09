# Datasets

## BOSSBase 1.01

The principal experiments use the public BOSSBase 1.01 corpus:

- 10,000 grayscale photographs;
- native resolution: `512 x 512`;
- image format used locally: PGM;
- official project page: <https://agents.fel.cvut.cz/boss/>.

The dataset is not redistributed in this repository. Place the extracted
images in a local directory and pass that path through `--dataset-root`.

The principal campaign applies channel transformations to native-resolution
images and resizes the transformed images to `128 x 128` only at the neural
encoder boundary.

## CIFAR-100

CIFAR-100 is used for the secondary controlled ablation and handcrafted
descriptor comparison. It can be obtained from:

<https://www.cs.toronto.edu/~kriz/cifar.html>

## Caltech-101

The cross-dataset evaluation uses all 9,144 RGB images from Caltech-101:

- variable original resolutions;
- official record: <https://data.caltech.edu/records/mzrjq-6wc02>;
- deterministic preparation script: `download_caltech101.py`.

The preparation script uses the `mteb/Caltech101` Hugging Face mirror as a
distribution channel while preserving CaltechDATA as the scientific
provenance. Images are centre-fitted to `256 x 256` in RGB for channel
simulation and resized to `128 x 128` only at the encoder boundary.

## Data Integrity

No synthetic images are used in the principal, cross-dataset, or secondary
experiments.
Deterministic seeds define the train/index partitions but do not alter the
source images.
