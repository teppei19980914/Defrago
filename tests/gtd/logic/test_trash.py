"""ゴミ箱ロジックのテスト."""

from datetime import UTC, datetime, timedelta

import pytest

from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.logic.trash import RETENTION_DAYS, TrashLogic
from study_python.gtd.models import (
    EnergyLevel,
    GtdItem,
    ItemStatus,
    Location,
    Tag,
    TaskStatus,
    TimeEstimate,
)
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

    def test_restore_resets_classification_for_task(
        self,
        trash: TrashLogic,
        repo: DbGtdRepository,
    ):
        """v3.1.4: タスクを復元するとタグ・ステータス・Context がクリアされる."""
        item = GtdItem(
            title="分類済みタスク",
            note="重要なメモ",
            item_status=ItemStatus.TRASH,
            tag=Tag.TASK,
            status=TaskStatus.IN_PROGRESS.value,
            locations=[Location.DESK, Location.HOME],
            time_estimate=TimeEstimate.WITHIN_30MIN,
            energy=EnergyLevel.HIGH,
            deleted_at="2026-04-01T00:00:00+00:00",
        )
        repo.add(item)

        result = trash.restore(item.id)
        assert result is not None
        # Inbox に戻る
        assert result.item_status == ItemStatus.INBOX
        assert result.deleted_at == ""
        # GTD 関連の状態は全クリア
        assert result.tag is None
        assert result.status is None
        assert result.locations == []
        assert result.time_estimate is None
        assert result.energy is None
        # 本質的な情報は保持
        assert result.title == "分類済みタスク"
        assert result.note == "重要なメモ"

    def test_restore_resets_project_state(
        self,
        trash: TrashLogic,
        repo: DbGtdRepository,
    ):
        """プロジェクトを復元すると、計画情報もすべてクリアされ Inbox の素になる."""
        project = GtdItem(
            title="計画済みプロジェクト",
            item_status=ItemStatus.TRASH,
            tag=Tag.PROJECT,
            project_purpose="効率化を実現する",
            project_outcome="月100時間削減",
            project_support_location="Google Drive",
            deleted_at="2026-04-01T00:00:00+00:00",
        )
        repo.add(project)

        result = trash.restore(project.id)
        assert result is not None
        assert result.item_status == ItemStatus.INBOX
        assert result.tag is None
        assert result.project_purpose == ""
        assert result.project_outcome == ""
        assert result.project_support_location == ""

    def test_restore_resets_subtask_parent_link(
        self,
        trash: TrashLogic,
        repo: DbGtdRepository,
    ):
        """サブタスクを復元すると親プロジェクトとの紐づけもクリアされる."""
        sub = GtdItem(
            title="計画から生成されたサブタスク",
            item_status=ItemStatus.TRASH,
            tag=Tag.TASK,
            status=TaskStatus.NOT_STARTED.value,
            parent_project_id="proj-xyz",
            parent_project_title="親プロジェクト",
            order=2,
            is_next_action=True,
            deadline="2026-04-15",
            deleted_at="2026-04-01T00:00:00+00:00",
        )
        repo.add(sub)

        result = trash.restore(sub.id)
        assert result is not None
        assert result.item_status == ItemStatus.INBOX
        assert result.tag is None
        # 親プロジェクトとの紐づけはクリアされる (一律 Inbox の素)
        assert result.parent_project_id is None
        assert result.parent_project_title == ""
        assert result.order is None
        assert result.is_next_action is False
        assert result.deadline == ""

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
