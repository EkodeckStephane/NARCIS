from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".pgm", ".tif", ".tiff"}


def discover_images(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def load_grayscale(path: Path, image_size: int) -> torch.Tensor:
    image = Image.open(path).convert("L").resize(
        (image_size, image_size), Image.Resampling.BICUBIC
    )
    array = np.asarray(image, dtype=np.float32) / 255.0
    return torch.from_numpy(array).unsqueeze(0)


class ImageCorpus(Dataset):
    def __init__(self, root: Path, image_size: int):
        self.paths = discover_images(root)
        if not self.paths:
            raise ValueError(f"No images found under {root}")
        self.image_size = image_size

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int) -> tuple[torch.Tensor, str]:
        path = self.paths[index]
        return load_grayscale(path, self.image_size), str(path)
