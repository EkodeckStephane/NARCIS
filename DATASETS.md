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

## Data Integrity

No synthetic images are used in the principal or secondary experiments.
Deterministic seeds define the train/index partitions but do not alter the
source images.
