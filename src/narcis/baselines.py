import numpy as np
import torch
from scipy.fft import dctn


def _arrays(images: torch.Tensor) -> np.ndarray:
    return images.squeeze(1).cpu().numpy()


def dct_descriptor(images: torch.Tensor, side: int = 16) -> np.ndarray:
    descriptors = []
    for image in _arrays(images):
        transformed = dctn(image, norm="ortho")[:side, :side].reshape(-1)
        transformed = transformed - transformed.mean()
        norm = np.linalg.norm(transformed)
        descriptors.append(transformed / max(norm, 1e-12))
    return np.asarray(descriptors, dtype=np.float32)


def histogram_descriptor(images: torch.Tensor, bins: int = 64) -> np.ndarray:
    descriptors = []
    for image in _arrays(images):
        histogram, _ = np.histogram(
            image, bins=bins, range=(0.0, 1.0), density=True
        )
        histogram = histogram.astype(np.float32)
        descriptors.append(histogram / max(np.linalg.norm(histogram), 1e-12))
    return np.asarray(descriptors, dtype=np.float32)
