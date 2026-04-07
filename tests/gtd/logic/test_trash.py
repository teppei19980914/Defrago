"""ゴミ箱ロジックのテスト."""

from datetime import UTC, datetime, timedelta

import pytest

from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.logic.trash import RETENTION_DAYS, TrashLogic
from study_python.gtd.models import GtdItem, ItemStatus
from study_python.gtd.web.db_repository import DbGtdRepository


@pytest.fixture
def trash(repo: DbGtdRepository) -> TrashLogic:
    return TrashLogic(repo)


@pytest.fixture
def collection(repo: DbGtdRepository) -> CollectionLogic:
    return CollectionLogic(repo)


class TestTrashLogic:
    """TrashLogicのテスト."""

    def test_get_trash_items_empty(self, trash: TrashLogic):
        assert trash.get_trash_items() == []

    def test_get_trash_items(
        self,
        trash: TrashLogic,
        collection: CollectionLogic,
        repo: DbGtdRepository,
    ):
        item = collection.add_to_inbox("削除対象")
        collection.move_to_trash(item.id)

        items = trash.get_trash_items()
        assert len(items) == 1
        assert items[0].title == "削除対象"

    def test_get_trash_items_excludes_inbox(
        self,
        trash: TrashLogic,
        collection: CollectionLogic,
        repo: DbGtdRepository,
    ):
        collection.add_to_inbox("Inbox")
        item = collection.add_to_inbox("ゴミ箱")
        collection.move_to_trash(item.id)

        items = trash.get_trash_items()
        assert len(items) == 1
        assert items[0].title == "ゴミ箱"

    def test_restore(
        self,
        trash: TrashLogic,
        collection: CollectionLogic,
    ):
        item = collection.add_to_inbox("復元対象")
        collection.move_to_trash(item.id)

        result = trash.restore(item.id)
        assert result is not None
        assert result.item_status == ItemStatus.INBOX
        assert result.deleted_at == ""

    def test_restore_nonexistent(self, trash: TrashLogic):
        assert trash.restore("nonexistent") is None

    def test_restore_non_trash_returns_none(
        self,
        trash: TrashLogic,
        collection: CollectionLogic,
    ):
        item = collection.add_to_inbox("Inbox内")
        result = trash.restore(item.id)
        assert result is None

    def test_delete_permanently(
        self,
        trash: TrashLogic,
        collection: CollectionLogic,
        repo: DbGtdRepository,
    ):
        item = collection.add_to_inbox("完全削除")
        collection.move_to_trash(item.id)

        result = trash.delete_permanently(item.id)
        assert result is not None
        assert repo.get(item.id) is None
        assert len(repo.items) == 0

    def test_delete_permanently_non_trash_returns_none(
        self,
        trash: TrashLogic,
        collection: CollectionLogic,
        repo: DbGtdRepository,
    ):
        item = collection.add_to_inbox("Inbox内")
        result = trash.delete_permanently(item.id)
        assert result is None
        assert len(repo.items) == 1

    def test_days_until_auto_delete_just_deleted(
        self,
        trash: TrashLogic,
        collection: CollectionLogic,
    ):
        item = collection.add_to_inbox("今削除")
        collection.move_to_trash(item.id)

        days = trash.days_until_auto_delete(item)
        assert days == RETENTION_DAYS

    def test_days_until_auto_delete_5_days_old(self, trash: TrashLogic):
        item = GtdItem(title="5日前削除", item_status=ItemStatus.TRASH)
        old_time = datetime.now(tz=UTC) - timedelta(days=5)
        item.deleted_at = old_time.isoformat()

        days = trash.days_until_auto_delete(item)
        assert days == RETENTION_DAYS - 5

    def test_days_until_auto_delete_expired(self, trash: TrashLogic):
        item = GtdItem(title="期限切れ", item_status=ItemStatus.TRASH)
        old_time = datetime.now(tz=UTC) - timedelta(days=RETENTION_DAYS + 5)
        item.deleted_at = old_time.isoformat()

        days = trash.days_until_auto_delete(item)
        assert days == 0

    def test_days_until_auto_delete_no_deleted_at(self, trash: TrashLogic):
        item = GtdItem(title="日時なし", item_status=ItemStatus.TRASH)
        days = trash.days_until_auto_delete(item)
        assert days == RETENTION_DAYS
