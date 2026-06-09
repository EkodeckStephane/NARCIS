from collections.abc import Callable
from pathlib import Path
from time import perf_counter

import numpy as np
import psutil
import torch
from sklearn.cluster import KMeans
from torch.utils.data import DataLoader

from .attacks import attack_suite
from .baselines import dct_descriptor, histogram_descriptor
from .data import ImageCorpus
from .index import NeuralCodebook


@torch.no_grad()
def neural_descriptor(
    model: torch.nn.Module, images: torch.Tensor
) -> np.ndarray:
    model.eval()
    return model(images).cpu().numpy()


def _load_all(root: Path, image_size: int) -> tuple[torch.Tensor, list[str]]:
    dataset = ImageCorpus(root, image_size)
    loader = DataLoader(dataset, batch_size=32, shuffle=False)
    images = []
    paths: list[str] = []
    for batch, batch_paths in loader:
        images.append(batch)
        paths.extend(batch_paths)
    return torch.cat(images), paths


def evaluate_descriptor(
    name: str,
    descriptor: Callable[[torch.Tensor], np.ndarray],
    images: torch.Tensor,
    clusters: int,
    seed: int,
    image_size: int,
) -> dict:
    started = perf_counter()
    clean_embeddings = descriptor(images)
    codebook = NeuralCodebook.fit(clean_embeddings, clusters, seed)
    clean_labels = codebook.predict(clean_embeddings)
    build_seconds = perf_counter() - started
    attacks = {}
    for attack_name, attack in attack_suite(image_size, seed).items():
        attacked = torch.stack([attack(image) for image in images])
        attacked_labels = codebook.predict(descriptor(attacked))
        attacks[attack_name] = float(np.mean(attacked_labels == clean_labels))
    counts = np.bincount(clean_labels, minlength=clusters)
    return {
        "descriptor": name,
        "clusters": clusters,
        "images": len(images),
        "build_seconds": build_seconds,
        "minimum_bucket_size": int(counts.min()),
        "maximum_bucket_size": int(counts.max()),
        "occupancy_cv": float(counts.std() / max(counts.mean(), 1e-12)),
        "attack_symbol_accuracy": attacks,
        "mean_attacked_accuracy": float(
            np.mean([value for key, value in attacks.items() if key != "clean"])
        ),
        "worst_attacked_accuracy": float(
            min(value for key, value in attacks.items() if key != "clean")
        ),
    }


def run_comparative_evaluation(
    model: torch.nn.Module,
    dataset_root: Path,
    image_size: int,
    clusters: int,
    seed: int,
) -> dict:
    images, _ = _load_all(dataset_root, image_size)
    process = psutil.Process()
    rss_before = process.memory_info().rss
    results = [
        evaluate_descriptor(
            "narcis_neural",
            lambda batch: neural_descriptor(model, batch),
            images,
            clusters,
            seed,
            image_size,
        ),
        evaluate_descriptor(
            "dct_16x16",
            dct_descriptor,
            images,
            clusters,
            seed,
            image_size,
        ),
        evaluate_descriptor(
            "gray_histogram_64",
            histogram_descriptor,
            images,
            clusters,
            seed,
            image_size,
        ),
    ]
    rss_after = process.memory_info().rss
    neural = results[0]
    best_baseline = max(
        results[1:], key=lambda result: result["mean_attacked_accuracy"]
    )
    return {
        "results": results,
        "neural_mean_margin_over_best_baseline": (
            neural["mean_attacked_accuracy"]
            - best_baseline["mean_attacked_accuracy"]
        ),
        "neural_worst_margin_over_best_baseline": (
            neural["worst_attacked_accuracy"]
            - best_baseline["worst_attacked_accuracy"]
        ),
        "rss_delta_bytes": max(0, rss_after - rss_before),
        "comparative_superiority_established": (
            neural["mean_attacked_accuracy"]
            > best_baseline["mean_attacked_accuracy"]
            and neural["worst_attacked_accuracy"]
            > best_baseline["worst_attacked_accuracy"]
        ),
        "scope": "local descriptor baselines; not published-SOTA superiority",
    }


def scalability_profile(
    embeddings: np.ndarray, seed: int, clusters: int
) -> list[dict]:
    rows = []
    for size in sorted(
        set(
            min(len(embeddings), requested)
            for requested in (32, 64, 128, 256, 512, 1024)
        )
    ):
        sample = embeddings[:size]
        started = perf_counter()
        KMeans(
            n_clusters=min(clusters, size),
            random_state=seed,
            n_init=10,
        ).fit(sample)
        rows.append(
            {
                "images": size,
                "fit_seconds": perf_counter() - started,
                "embedding_bytes": int(sample.nbytes),
            }
        )
    return rows
