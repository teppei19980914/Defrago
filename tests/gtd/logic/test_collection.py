"""収集ロジックのテスト."""

from pathlib import Path

import pytest

from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.models import ItemStatus
from study_python.gtd.repository import GtdRepository


@pytest.fixture
def repo(tmp_path: Path) -> GtdRepository:
    return GtdRepository(data_path=tmp_path / "test.json")


@pytest.fixture
def logic(repo: GtdRepository) -> CollectionLogic:
    return CollectionLogic(repo)


class TestCollectionLogic:
    """CollectionLogicのテスト."""

    def test_add_to_inbox(self, logic: CollectionLogic, repo: GtdRepository):
        item = logic.add_to_inbox("新しいアイテム")
        assert item.title == "新しいアイテム"
        assert item.item_status == ItemStatus.INBOX
        assert len(repo.items) == 1

    def test_add_to_inbox_with_note(self, logic: CollectionLogic):
        item = logic.add_to_inbox("アイテム", note="メモ")
        assert item.note == "メモ"

    def test_add_to_inbox_strips_whitespace(self, logic: CollectionLogic):
        item = logic.add_to_inbox("  スペース付き  ", note="  メモ  ")
        assert item.title == "スペース付き"
        assert item.note == "メモ"

    def test_add_to_inbox_empty_title_raises(self, logic: CollectionLogic):
        with pytest.raises(ValueError, match="タイトルは必須です"):
            logic.add_to_inbox("")

    def test_add_to_inbox_whitespace_only_raises(self, logic: CollectionLogic):
        with pytest.raises(ValueError, match="タイトルは必須です"):
            logic.add_to_inbox("   ")

    def test_delete_item(self, logic: CollectionLogic, repo: GtdRepository):
        item = logic.add_to_inbox("削除対象")
        result = logic.delete_item(item.id)
        assert result is not None
        assert result.title == "削除対象"
        assert len(repo.items) == 0

    def test_delete_nonexistent_item(self, logic: CollectionLogic):
        result = logic.delete_item("nonexistent")
        assert result is None

    def test_move_to_reference(self, logic: CollectionLogic):
        item = logic.add_to_inbox("参考資料にする")
        result = logic.move_to_reference(item.id)
        assert result is not None
        assert result.item_status == ItemStatus.REFERENCE

    def test_move_to_reference_nonexistent(self, logic: CollectionLogic):
        result = logic.move_to_reference("nonexistent")
        assert result is None

    def test_move_to_someday(self, logic: CollectionLogic):
        item = logic.add_to_inbox("いつかやる")
        result = logic.move_to_someday(item.id)
        assert result is not None
        assert result.item_status == ItemStatus.SOMEDAY

    def test_move_to_someday_nonexistent(self, logic: CollectionLogic):
        result = logic.move_to_someday("nonexistent")
        assert result is None

    def test_get_inbox_items(self, logic: CollectionLogic):
        logic.add_to_inbox("アイテム1")
        logic.add_to_inbox("アイテム2")
        item3 = logic.add_to_inbox("アイテム3")
        logic.move_to_someday(item3.id)

        inbox_items = logic.get_inbox_items()
        assert len(inbox_items) == 2

    def test_get_someday_items(self, logic: CollectionLogic):
        item = logic.add_to_inbox("いつか")
        logic.move_to_someday(item.id)

        someday_items = logic.get_someday_items()
        assert len(someday_items) == 1
        assert someday_items[0].title == "いつか"

    def test_get_reference_items(self, logic: CollectionLogic):
        item = logic.add_to_inbox("参考")
        logic.move_to_reference(item.id)

        ref_items = logic.get_reference_items()
        assert len(ref_items) == 1
        assert ref_items[0].title == "参考"
