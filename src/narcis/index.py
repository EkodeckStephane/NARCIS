from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from sklearn.cluster import KMeans
from torch.utils.data import DataLoader

from .data import ImageCorpus


@dataclass
class NeuralCodebook:
    centroids: np.ndarray

    @property
    def size(self) -> int:
        return int(self.centroids.shape[0])

    def predict(self, embeddings: np.ndarray) -> np.ndarray:
        distances = np.linalg.norm(
            embeddings[:, None, :] - self.centroids[None, :, :], axis=2
        )
        return distances.argmin(axis=1)

    def confidence(self, embeddings: np.ndarray) -> np.ndarray:
        distances = np.linalg.norm(
            embeddings[:, None, :] - self.centroids[None, :, :], axis=2
        )
        nearest = np.partition(distances, 1, axis=1)[:, :2]
        return nearest[:, 1] - nearest[:, 0]

    @classmethod
    def fit(
        cls, embeddings: np.ndarray, clusters: int, seed: int
    ) -> "NeuralCodebook":
        if clusters < 2 or clusters > len(embeddings):
            raise ValueError("clusters must be between 2 and the corpus size")
        model = KMeans(n_clusters=clusters, random_state=seed, n_init=20)
        model.fit(embeddings)
        centroids = model.cluster_centers_.astype(np.float32)
        centroids /= np.maximum(
            np.linalg.norm(centroids, axis=1, keepdims=True), 1e-12
        )
        return cls(centroids)


@dataclass
class QuantileCodebook:
    mean: np.ndarray
    direction: np.ndarray
    boundaries: np.ndarray

    @property
    def size(self) -> int:
        return int(len(self.boundaries) + 1)

    @classmethod
    def fit(
        cls, embeddings: np.ndarray, clusters: int
    ) -> "QuantileCodebook":
        if clusters < 2 or clusters > len(embeddings):
            raise ValueError("clusters must be between 2 and the corpus size")
        mean = embeddings.mean(axis=0)
        centered = embeddings - mean
        _, _, right = np.linalg.svd(centered, full_matrices=False)
        direction = right[0].astype(np.float32)
        return cls.fit_direction(embeddings, clusters, direction)

    @classmethod
    def fit_direction(
        cls,
        embeddings: np.ndarray,
        clusters: int,
        direction: np.ndarray,
    ) -> "QuantileCodebook":
        if clusters < 2 or clusters > len(embeddings):
            raise ValueError("clusters must be between 2 and the corpus size")
        direction = np.asarray(direction, dtype=np.float32)
        if direction.shape != (embeddings.shape[1],):
            raise ValueError("direction must match the embedding dimension")
        norm = float(np.linalg.norm(direction))
        if norm <= 1e-12:
            raise ValueError("direction must have non-zero norm")
        direction = direction / norm
        mean = embeddings.mean(axis=0).astype(np.float32)
        projection = (embeddings - mean) @ direction
        boundaries = np.quantile(
            projection,
            np.arange(1, clusters) / clusters,
        ).astype(np.float32)
        return cls(mean, direction, boundaries)

    def project(self, embeddings: np.ndarray) -> np.ndarray:
        return (embeddings - self.mean) @ self.direction

    def predict(self, embeddings: np.ndarray) -> np.ndarray:
        return np.digitize(self.project(embeddings), self.boundaries)

    def confidence(self, embeddings: np.ndarray) -> np.ndarray:
        projection = self.project(embeddings)
        distances = np.abs(
            projection[:, None] - self.boundaries[None, :]
        )
        return distances.min(axis=1)


@dataclass
class CoverIndex:
    buckets: dict[int, list[str]]
    labels: dict[str, int]

    @classmethod
    def build(
        cls, paths: list[str], labels: np.ndarray
    ) -> "CoverIndex":
        buckets: dict[int, list[str]] = defaultdict(list)
        label_map: dict[str, int] = {}
        for path, label in zip(paths, labels, strict=True):
            numeric = int(label)
            buckets[numeric].append(path)
            label_map[path] = numeric
        return cls(dict(buckets), label_map)

    def minimum_bucket_size(self, expected_labels: int) -> int:
        return min(len(self.buckets.get(label, [])) for label in range(expected_labels))


@torch.no_grad()
def embed_corpus(
    model: torch.nn.Module,
    root: Path,
    image_size: int,
    batch_size: int = 32,
) -> tuple[np.ndarray, list[str]]:
    dataset = ImageCorpus(root, image_size)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    model.eval()
    embeddings: list[np.ndarray] = []
    paths: list[str] = []
    for images, batch_paths in loader:
        embeddings.append(model(images).cpu().numpy())
        paths.extend(batch_paths)
    return np.concatenate(embeddings, axis=0), paths
