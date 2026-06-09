import torch
from torch import nn
from torch.nn import functional as F


class ConvBlock(nn.Sequential):
    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__(
            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=3,
                stride=stride,
                padding=1,
                bias=False,
            ),
            nn.BatchNorm2d(out_channels),
            nn.SiLU(inplace=True),
            nn.Conv2d(
                out_channels,
                out_channels,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            nn.BatchNorm2d(out_channels),
            nn.SiLU(inplace=True),
        )


class RobustImageEncoder(nn.Module):
    def __init__(
        self,
        embedding_dim: int = 64,
        base_channels: int = 24,
        in_channels: int = 1,
    ):
        super().__init__()
        c = base_channels
        self.backbone = nn.Sequential(
            ConvBlock(in_channels, c),
            ConvBlock(c, 2 * c, stride=2),
            ConvBlock(2 * c, 4 * c, stride=2),
            ConvBlock(4 * c, 6 * c, stride=2),
            nn.AdaptiveAvgPool2d(1),
        )
        self.projector = nn.Sequential(
            nn.Flatten(),
            nn.Linear(6 * c, 2 * embedding_dim),
            nn.SiLU(inplace=True),
            nn.Linear(2 * embedding_dim, embedding_dim),
        )

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        return F.normalize(self.projector(self.backbone(images)), dim=1)
