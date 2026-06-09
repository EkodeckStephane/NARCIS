from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    image_size: int = 128
    embedding_dim: int = 64
    base_channels: int = 24


@dataclass(frozen=True)
class TrainingConfig:
    epochs: int = 2
    batch_size: int = 16
    learning_rate: float = 1e-3
    weight_decay: float = 1e-5
    invariance_weight: float = 25.0
    variance_weight: float = 25.0
    covariance_weight: float = 1.0
    seed: int = 20260608
