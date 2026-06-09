import io
import random

import numpy as np
import torch
import torchvision.transforms.functional as TF
from PIL import Image, ImageFilter


class ChannelAugment:
    """Stochastic channel simulator for descriptor-invariance training."""

    def __init__(self, image_size: int, seed: int | None = None):
        self.image_size = image_size
        self.random = random.Random(seed)

    def __call__(self, tensor: torch.Tensor) -> torch.Tensor:
        image = TF.to_pil_image(tensor)
        operation = self.random.choice(
            ("jpeg", "noise", "blur", "resize", "crop", "rotate", "identity")
        )

        if operation == "jpeg":
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=self.random.randint(55, 90))
            buffer.seek(0)
            image = Image.open(buffer).convert(image.mode)
        elif operation == "noise":
            array = np.asarray(image, dtype=np.float32)
            sigma = self.random.uniform(2.0, 15.0)
            noise = np.random.default_rng(self.random.randrange(2**32)).normal(
                0.0, sigma, array.shape
            )
            image = Image.fromarray(np.clip(array + noise, 0, 255).astype(np.uint8))
        elif operation == "blur":
            image = image.filter(
                ImageFilter.GaussianBlur(radius=self.random.uniform(0.3, 1.8))
            )
        elif operation == "resize":
            scale = self.random.uniform(0.65, 0.95)
            side = max(16, int(self.image_size * scale))
            image = image.resize((side, side), Image.Resampling.BILINEAR)
        elif operation == "crop":
            margin = self.random.randint(2, max(2, self.image_size // 10))
            image = image.crop(
                (margin, margin, image.width - margin, image.height - margin)
            )
        elif operation == "rotate":
            image = image.rotate(
                self.random.uniform(-8.0, 8.0),
                resample=Image.Resampling.BILINEAR,
                fillcolor=(0, 0, 0) if image.mode == "RGB" else 0,
            )

        image = image.resize(
            (self.image_size, self.image_size), Image.Resampling.BICUBIC
        )
        return TF.to_tensor(image)
