import torch

from narcis.attacks import attack_suite
from narcis.augment import ChannelAugment


def test_attack_suite_preserves_rgb_channels():
    image = torch.rand(3, 64, 64)
    for attack in attack_suite(64, seed=11).values():
        assert attack(image).shape == image.shape


def test_channel_augment_preserves_rgb_channels():
    image = torch.rand(3, 64, 64)
    augment = ChannelAugment(64, seed=11)
    for _ in range(20):
        assert augment(image).shape == image.shape
