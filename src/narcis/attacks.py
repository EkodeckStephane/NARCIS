import io
from collections.abc import Callable

import numpy as np
import torch
import torchvision.transforms.functional as TF
from PIL import Image, ImageFilter


Attack = Callable[[torch.Tensor], torch.Tensor]


def _pil(tensor: torch.Tensor) -> Image.Image:
    return TF.to_pil_image(tensor)


def _tensor(image: Image.Image, size: int, mode: str) -> torch.Tensor:
    return TF.to_tensor(
        image.convert(mode).resize((size, size), Image.Resampling.BICUBIC)
    )


def attack_suite(image_size: int, seed: int = 20260608) -> dict[str, Attack]:
    def mode(tensor: torch.Tensor) -> str:
        return "RGB" if tensor.shape[0] == 3 else "L"

    def jpeg(quality: int) -> Attack:
        def apply(tensor: torch.Tensor) -> torch.Tensor:
            buffer = io.BytesIO()
            _pil(tensor).save(buffer, format="JPEG", quality=quality)
            buffer.seek(0)
            return _tensor(Image.open(buffer), image_size, mode(tensor))

        return apply

    def noise(sigma: float, local_seed: int) -> Attack:
        rng = np.random.default_rng(local_seed)

        def apply(tensor: torch.Tensor) -> torch.Tensor:
            image = _pil(tensor)
            array = np.asarray(image, dtype=np.float32)
            damaged = np.clip(
                array + rng.normal(0.0, sigma, array.shape), 0, 255
            )
            return _tensor(
                Image.fromarray(damaged.astype(np.uint8)),
                image_size,
                mode(tensor),
            )

        return apply

    def blur(radius: float) -> Attack:
        return lambda tensor: _tensor(
            _pil(tensor).filter(ImageFilter.GaussianBlur(radius)),
            image_size,
            mode(tensor),
        )

    def rotate(angle: float) -> Attack:
        return lambda tensor: _tensor(
            _pil(tensor).rotate(
                angle,
                resample=Image.Resampling.BILINEAR,
                fillcolor=(0, 0, 0) if tensor.shape[0] == 3 else 0,
            ),
            image_size,
            mode(tensor),
        )

    def crop(fraction: float) -> Attack:
        def apply(tensor: torch.Tensor) -> torch.Tensor:
            image = _pil(tensor)
            margin = int(image.width * fraction)
            return _tensor(
                image.crop(
                    (
                        margin,
                        margin,
                        image.width - margin,
                        image.height - margin,
                    )
                ),
                image_size,
                mode(tensor),
            )

        return apply

    def resize(scale: float) -> Attack:
        def apply(tensor: torch.Tensor) -> torch.Tensor:
            image = _pil(tensor)
            side = max(16, int(image_size * scale))
            reduced = image.resize(
                (side, side), Image.Resampling.BILINEAR
            )
            return _tensor(reduced, image_size, mode(tensor))

        return apply

    return {
        "clean": lambda tensor: tensor.clone(),
        "jpeg_80": jpeg(80),
        "jpeg_50": jpeg(50),
        "gaussian_5": noise(5.0, seed + 1),
        "gaussian_12": noise(12.0, seed + 2),
        "gaussian_9_holdout": noise(9.0, seed + 3),
        "gaussian_15_holdout": noise(15.0, seed + 4),
        "blur_0.8": blur(0.8),
        "blur_1.5": blur(1.5),
        "blur_1.2_holdout": blur(1.2),
        "blur_1.8_holdout": blur(1.8),
        "resize_075": resize(0.75),
        "resize_050": resize(0.50),
        "crop_05": crop(0.05),
        "crop_10": crop(0.10),
        "crop_08_holdout": crop(0.08),
        "crop_12_holdout": crop(0.12),
        "rotate_3": rotate(3.0),
        "rotate_7": rotate(7.0),
        "rotate_5_holdout": rotate(5.0),
        "rotate_9_holdout": rotate(9.0),
    }
