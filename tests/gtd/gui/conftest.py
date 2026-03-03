"""GUI テスト用 fixtures."""

from pathlib import Path

import pytest

from study_python.gtd.repository import GtdRepository


@pytest.fixture
def repo(tmp_path: Path) -> GtdRepository:
    """テスト用リポジトリを返す."""
    return GtdRepository(data_path=tmp_path / "test.json")
