from pathlib import Path

from narcis.data import IMAGE_SUFFIXES


def test_pgm_is_supported_for_bossbase():
    assert Path("cover.pgm").suffix in IMAGE_SUFFIXES
