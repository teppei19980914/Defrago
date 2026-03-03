"""pytest の共通設定とフィクスチャ."""

import pytest


@pytest.fixture
def sample_numbers() -> tuple[int, int]:
    """テスト用のサンプル数値ペアを提供するフィクスチャ。

    Returns:
        テスト用の数値ペア (10, 5)。
    """
    return (10, 5)
