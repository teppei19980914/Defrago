"""収集ロジックのテスト."""

import pytest

from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.models import GtdItem, ItemStatus, Tag
from study_python.gtd.web.db_repository import DbGtdRepository


@pytest.fixture
def logic(repo: DbGtdRepository) -> CollectionLogic:
    return CollectionLogic(repo)


class TestCollectionLogic:
    """CollectionLogicのテスト."""

    def test_add_to_inbox(self, logic: CollectionLogic, repo: DbGtdRepository):
        item = logic.add_to_inbox("新しいアイテム")
        assert item.title == "新しいアイテム"
        assert item.item_status == ItemStatus.INBOX
        assert item.tag is None
        assert len(repo.items) == 1

    def test_add_to_inbox_with_tag_classifies(self, logic: CollectionLogic):
        item = logic.add_to_inbox("即実行タスク", tag=Tag.DO_NOW)
        assert item.tag == Tag.DO_NOW
        assert item.status == "not_started"

    def test_add_to_inbox_with_project_tag(self, logic: CollectionLogic):
        item = logic.add_to_inbox("プロジェクト", tag=Tag.PROJECT)
        assert item.tag == Tag.PROJECT
        assert item.status is None

    def test_add_to_inbox_with_task_tag(self, logic: CollectionLogic):
        item = logic.add_to_inbox("タスク", tag=Tag.TASK)
        assert item.tag == Tag.TASK
        assert item.status == "not_started"

    def test_add_to_inbox_with_delegation_tag(self, logic: CollectionLogic):
        item = logic.add_to_inbox("委任", tag=Tag.DELEGATION)
        assert item.tag == Tag.DELEGATION
        assert item.status == "not_started"

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

    def test_move_to_trash(self, logic: CollectionLogic, repo: DbGtdRepository):
        item = logic.add_to_inbox("削除対象")
        result = logic.move_to_trash(item.id)
        assert result is not None
        assert result.item_status == ItemStatus.TRASH
        assert result.deleted_at != ""
        # アイテムは残る（物理削除されない）
        assert len(repo.items) == 1

    def test_move_to_trash_nonexistent(self, logic: CollectionLogic):
        result = logic.move_to_trash("nonexistent")
        assert result is None

    def test_get_inbox_items(self, logic: CollectionLogic):
        logic.add_to_inbox("アイテム1")
        logic.add_to_inbox("アイテム2")
        item3 = logic.add_to_inbox("アイテム3")
        logic.move_to_trash(item3.id)

        inbox_items = logic.get_inbox_items()
        assert len(inbox_items) == 2

    def test_get_unclassified_inbox_items(self, logic: CollectionLogic):
        logic.add_to_inbox("未分類1")
        logic.add_to_inbox("未分類2")
        logic.add_to_inbox("分類済み", tag=Tag.DO_NOW)

        unclassified = logic.get_unclassified_inbox_items()
        assert len(unclassified) == 2


class TestReorderItem:
    """reorder_itemのテスト."""

    def _create_project_items(
        self, repo: DbGtdRepository, project_id: str = "proj-1"
    ) -> list[GtdItem]:
        items = []
        for i, title in enumerate(["A", "B", "C"]):
            item = GtdItem(
                title=title,
                parent_project_id=project_id,
                parent_project_title="PJ",
                order=i,
            )
            repo.add(item)
            items.append(item)
        return items

    def test_reorder_up(self, logic: CollectionLogic, repo: DbGtdRepository):
        items = self._create_project_items(repo)
        result = logic.reorder_item(items[1].id, "up")
        assert result is True
        assert items[1].order == 0
        assert items[0].order == 1

    def test_reorder_down(self, logic: CollectionLogic, repo: DbGtdRepository):
        items = self._create_project_items(repo)
        result = logic.reorder_item(items[0].id, "down")
        assert result is True
        assert items[0].order == 1
        assert items[1].order == 0

    def test_reorder_up_first_item_fails(
        self, logic: CollectionLogic, repo: DbGtdRepository
    ):
        items = self._create_project_items(repo)
        result = logic.reorder_item(items[0].id, "up")
        assert result is False

    def test_reorder_down_last_item_fails(
        self, logic: CollectionLogic, repo: DbGtdRepository
    ):
        items = self._create_project_items(repo)
        result = logic.reorder_item(items[2].id, "down")
        assert result is False

    def test_reorder_no_parent_project(
        self, logic: CollectionLogic, repo: DbGtdRepository
    ):
        item = GtdItem(title="通常")
        repo.add(item)
        result = logic.reorder_item(item.id, "up")
        assert result is False

    def test_reorder_nonexistent(self, logic: CollectionLogic):
        result = logic.reorder_item("nonexistent", "up")
        assert result is False

    def test_reorder_different_projects_independent(
        self, logic: CollectionLogic, repo: DbGtdRepository
    ):
        self._create_project_items(repo, "proj-1")
        items_b = self._create_project_items(repo, "proj-2")
        result = logic.reorder_item(items_b[1].id, "up")
        assert result is True
        assert items_b[1].order == 0
        assert items_b[0].order == 1
