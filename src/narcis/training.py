from dataclasses import asdict
from pathlib import Path
import json
import random

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from .augment import ChannelAugment
from .config import ModelConfig, TrainingConfig
from .data import ImageCorpus
from .model import RobustImageEncoder


def _off_diagonal(matrix: torch.Tensor) -> torch.Tensor:
    n = matrix.shape[0]
    return matrix.flatten()[:-1].view(n - 1, n + 1)[:, 1:].flatten()


def representation_loss(
    first: torch.Tensor,
    second: torch.Tensor,
    config: TrainingConfig,
) -> tuple[torch.Tensor, dict[str, float]]:
    invariance = nn.functional.mse_loss(first, second)
    eps = 1e-4
    target_std = first.shape[1] ** -0.5
    std_first = torch.sqrt(first.var(dim=0) + eps)
    std_second = torch.sqrt(second.var(dim=0) + eps)
    variance = torch.mean(
        nn.functional.relu(target_std - std_first)
    ) + torch.mean(
        nn.functional.relu(target_std - std_second)
    )

    first_centered = first - first.mean(dim=0)
    second_centered = second - second.mean(dim=0)
    denom = max(1, first.shape[0] - 1)
    covariance = (
        _off_diagonal(first_centered.T @ first_centered / denom).pow(2).mean()
        + _off_diagonal(second_centered.T @ second_centered / denom).pow(2).mean()
    )

    total = (
        config.invariance_weight * invariance
        + config.variance_weight * variance
        + config.covariance_weight * covariance
    )
    metrics = {
        "loss": float(total.detach()),
        "invariance": float(invariance.detach()),
        "variance": float(variance.detach()),
        "covariance": float(covariance.detach()),
    }
    return total, metrics


def train_encoder(
    dataset_root: Path,
    output_dir: Path,
    model_config: ModelConfig,
    training_config: TrainingConfig,
) -> tuple[RobustImageEncoder, list[dict[str, float]]]:
    random.seed(training_config.seed)
    np.random.seed(training_config.seed)
    torch.manual_seed(training_config.seed)

    dataset = ImageCorpus(dataset_root, model_config.image_size)
    loader = DataLoader(
        dataset,
        batch_size=training_config.batch_size,
        shuffle=True,
        drop_last=len(dataset) >= training_config.batch_size,
    )
    augment = ChannelAugment(model_config.image_size, training_config.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = RobustImageEncoder(
        model_config.embedding_dim, model_config.base_channels
    ).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=training_config.learning_rate,
        weight_decay=training_config.weight_decay,
    )

    history: list[dict[str, float]] = []
    model.train()
    for epoch in range(training_config.epochs):
        totals: dict[str, float] = {}
        batches = 0
        for images, _ in loader:
            first = torch.stack([augment(image) for image in images]).to(device)
            second = torch.stack([augment(image) for image in images]).to(device)
            optimizer.zero_grad(set_to_none=True)
            loss, metrics = representation_loss(
                model(first), model(second), training_config
            )
            loss.backward()
            optimizer.step()
            batches += 1
            for key, value in metrics.items():
                totals[key] = totals.get(key, 0.0) + value
        epoch_metrics = {
            "epoch": float(epoch + 1),
            **{key: value / max(1, batches) for key, value in totals.items()},
        }
        history.append(epoch_metrics)

    output_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_dir / "encoder.pt")
    (output_dir / "training_history.json").write_text(
        json.dumps(history, indent=2), encoding="utf-8"
    )
    (output_dir / "configuration.json").write_text(
        json.dumps(
            {
                "model": asdict(model_config),
                "training": asdict(training_config),
                "device": str(device),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return model.cpu(), history
