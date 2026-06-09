from collections.abc import Sequence
from pathlib import Path

import numpy as np
import torch
import torchvision.transforms.functional as TF
from torch.utils.data import Dataset
from torchvision.datasets import CIFAR100


class CifarPartition(Dataset):
    def __init__(
        self,
        root: Path,
        train: bool,
        indices: Sequence[int],
        image_size: int,
    ):
        self.dataset = CIFAR100(
            root=str(root), train=train, download=False
        )
        self.indices = list(map(int, indices))
        self.image_size = image_size

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, offset: int) -> tuple[torch.Tensor, str]:
        index = self.indices[offset]
        image, _ = self.dataset[index]
        image = image.convert("L").resize(
            (self.image_size, self.image_size)
        )
        return TF.to_tensor(image), f"cifar_{int(self.dataset.train)}_{index}"


def deterministic_partitions(
    seed: int,
    train_count: int,
    index_count: int,
    test_count: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_order = rng.permutation(50_000)
    test_order = rng.permutation(10_000)
    if train_count + index_count > len(train_order):
        raise ValueError("Requested train/index partition exceeds CIFAR train set")
    return (
        train_order[:train_count],
        train_order[train_count : train_count + index_count],
        test_order[:test_count],
    )
