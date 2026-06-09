import torch

from narcis.config import TrainingConfig
from narcis.model import RobustImageEncoder
from narcis.training import representation_loss


def test_encoder_produces_normalized_embeddings():
    model = RobustImageEncoder(embedding_dim=16, base_channels=4)
    embeddings = model(torch.rand(3, 1, 64, 64))
    assert embeddings.shape == (3, 16)
    assert torch.allclose(
        embeddings.norm(dim=1), torch.ones(3), atol=1e-5
    )


def test_encoder_accepts_rgb_images_when_configured():
    model = RobustImageEncoder(
        embedding_dim=16,
        base_channels=4,
        in_channels=3,
    )
    embeddings = model(torch.rand(3, 3, 64, 64))
    assert embeddings.shape == (3, 16)
    assert torch.allclose(
        embeddings.norm(dim=1), torch.ones(3), atol=1e-5
    )


def test_representation_loss_is_finite():
    first = torch.randn(8, 16)
    second = first + 0.01 * torch.randn(8, 16)
    loss, metrics = representation_loss(first, second, TrainingConfig())
    assert torch.isfinite(loss)
    assert set(metrics) == {"loss", "invariance", "variance", "covariance"}
