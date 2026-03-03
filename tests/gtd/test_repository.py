"""GTDリポジトリのテスト."""

import json
from pathlib import Path

import pytest

from study_python.gtd.models import (
    EnergyLevel,
    GtdItem,
    ItemStatus,
    Location,
    Tag,
    TaskStatus,
    TimeEstimate,
)
from study_python.gtd.repository import GtdRepository


@pytest.fixture
def tmp_data_path(tmp_path: Path) -> Path:
    """一時データファイルパスを返す."""
    return tmp_path / "test_data.json"


@pytest.fixture
def repo(tmp_data_path: Path) -> GtdRepository:
    """テスト用リポジトリを返す."""
    return GtdRepository(data_path=tmp_data_path)


class TestGtdRepository:
    """GtdRepositoryのテスト."""

    def test_init_with_default_path(self):
        repo = GtdRepository()
        assert repo.data_path.name == "gtd_data.json"

    def test_init_with_custom_path(self, tmp_data_path: Path):
        repo = GtdRepository(data_path=tmp_data_path)
        assert repo.data_path == tmp_data_path

    def test_load_empty_when_file_not_exists(self, repo: GtdRepository):
        items = repo.load()
        assert items == []

    def test_add_and_save(self, repo: GtdRepository, tmp_data_path: Path):
        item = GtdItem(title="テストアイテム")
        repo.add(item)
        repo.save()
        assert tmp_data_path.exists()

        raw = tmp_data_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert len(data) == 1
        assert data[0]["title"] == "テストアイテム"

    def test_save_and_load_roundtrip(self, repo: GtdRepository):
        item = GtdItem(
            title="完全なアイテム",
            item_status=ItemStatus.SOMEDAY,
            tag=Tag.TASK,
            status=TaskStatus.IN_PROGRESS.value,
            locations=[Location.DESK, Location.HOME],
            time_estimate=TimeEstimate.WITHIN_30MIN,
            energy=EnergyLevel.HIGH,
            importance=8,
            urgency=3,
            note="テストメモ",
        )
        repo.add(item)
        repo.save()

        repo2 = GtdRepository(data_path=repo.data_path)
        loaded = repo2.load()
        assert len(loaded) == 1
        loaded_item = loaded[0]
        assert loaded_item.title == "完全なアイテム"
        assert loaded_item.item_status == ItemStatus.SOMEDAY
        assert loaded_item.tag == Tag.TASK
        assert loaded_item.status == TaskStatus.IN_PROGRESS.value
        assert loaded_item.locations == [Location.DESK, Location.HOME]
        assert loaded_item.time_estimate == TimeEstimate.WITHIN_30MIN
        assert loaded_item.energy == EnergyLevel.HIGH
        assert loaded_item.importance == 8
        assert loaded_item.urgency == 3
        assert loaded_item.note == "テストメモ"

    def test_save_and_load_item_with_none_fields(self, repo: GtdRepository):
        item = GtdItem(title="シンプル")
        repo.add(item)
        repo.save()

        repo2 = GtdRepository(data_path=repo.data_path)
        loaded = repo2.load()
        assert len(loaded) == 1
        assert loaded[0].tag is None
        assert loaded[0].status is None
        assert loaded[0].time_estimate is None
        assert loaded[0].energy is None
        assert loaded[0].importance is None
        assert loaded[0].urgency is None

    def test_load_corrupted_file(self, tmp_data_path: Path):
        tmp_data_path.write_text("not json", encoding="utf-8")
        repo = GtdRepository(data_path=tmp_data_path)
        items = repo.load()
        assert items == []

    def test_remove_existing_item(self, repo: GtdRepository):
        item = GtdItem(title="削除対象")
        repo.add(item)
        removed = repo.remove(item.id)
        assert removed is not None
        assert removed.title == "削除対象"
        assert len(repo.items) == 0

    def test_remove_nonexistent_item(self, repo: GtdRepository):
        removed = repo.remove("nonexistent-id")
        assert removed is None

    def test_get_existing_item(self, repo: GtdRepository):
        item = GtdItem(title="検索対象")
        repo.add(item)
        found = repo.get(item.id)
        assert found is not None
        assert found.title == "検索対象"

    def test_get_nonexistent_item(self, repo: GtdRepository):
        found = repo.get("nonexistent-id")
        assert found is None

    def test_get_by_status(self, repo: GtdRepository):
        item1 = GtdItem(title="Inbox1", item_status=ItemStatus.INBOX)
        item2 = GtdItem(title="Someday1", item_status=ItemStatus.SOMEDAY)
        item3 = GtdItem(title="Inbox2", item_status=ItemStatus.INBOX)
        repo.add(item1)
        repo.add(item2)
        repo.add(item3)

        inbox_items = repo.get_by_status(ItemStatus.INBOX)
        assert len(inbox_items) == 2

        someday_items = repo.get_by_status(ItemStatus.SOMEDAY)
        assert len(someday_items) == 1

    def test_get_by_tag(self, repo: GtdRepository):
        item1 = GtdItem(title="タスク1", tag=Tag.TASK)
        item2 = GtdItem(title="依頼1", tag=Tag.DELEGATION)
        item3 = GtdItem(title="タスク2", tag=Tag.TASK)
        repo.add(item1)
        repo.add(item2)
        repo.add(item3)

        task_items = repo.get_by_tag(Tag.TASK)
        assert len(task_items) == 2

        delegation_items = repo.get_by_tag(Tag.DELEGATION)
        assert len(delegation_items) == 1

    def test_get_tasks(self, repo: GtdRepository):
        item1 = GtdItem(title="未タスク")
        item2 = GtdItem(title="タスク化済み", tag=Tag.TASK)
        item3 = GtdItem(title="プロジェクト", tag=Tag.PROJECT)
        repo.add(item1)
        repo.add(item2)
        repo.add(item3)

        tasks = repo.get_tasks()
        assert len(tasks) == 2  # tag付きのみ

    def test_items_property(self, repo: GtdRepository):
        assert repo.items == []
        item = GtdItem(title="テスト")
        repo.add(item)
        assert len(repo.items) == 1
