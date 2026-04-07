"""DbGtdRepositoryのテスト."""

from study_python.gtd.models import GtdItem, ItemStatus, Tag, TaskStatus
from study_python.gtd.web.db_repository import DbGtdRepository


class TestDbGtdRepository:
    """DbGtdRepositoryのテスト."""

    def test_empty_repository(self, test_session):
        repo = DbGtdRepository(test_session)
        assert repo.items == []

    def test_add_and_flush(self, test_session):
        repo = DbGtdRepository(test_session)
        item = GtdItem(title="テスト")
        repo.add(item)
        repo.flush_to_db()
        test_session.commit()

        # 再読み込みで確認
        repo2 = DbGtdRepository(test_session)
        assert len(repo2.items) == 1
        assert repo2.items[0].title == "テスト"

    def test_remove(self, test_session):
        repo = DbGtdRepository(test_session)
        item = GtdItem(title="削除対象")
        repo.add(item)
        removed = repo.remove(item.id)
        assert removed is not None
        assert removed.title == "削除対象"
        assert len(repo.items) == 0

    def test_remove_nonexistent(self, test_session):
        repo = DbGtdRepository(test_session)
        assert repo.remove("nonexistent") is None

    def test_get(self, test_session):
        repo = DbGtdRepository(test_session)
        item = GtdItem(title="検索対象")
        repo.add(item)
        found = repo.get(item.id)
        assert found is not None
        assert found.title == "検索対象"

    def test_get_nonexistent(self, test_session):
        repo = DbGtdRepository(test_session)
        assert repo.get("nonexistent") is None

    def test_get_by_status(self, test_session):
        repo = DbGtdRepository(test_session)
        repo.add(GtdItem(title="Inbox", item_status=ItemStatus.INBOX))
        repo.add(GtdItem(title="Someday", item_status=ItemStatus.SOMEDAY))
        assert len(repo.get_by_status(ItemStatus.INBOX)) == 1

    def test_get_by_tag(self, test_session):
        repo = DbGtdRepository(test_session)
        repo.add(
            GtdItem(title="タスク", tag=Tag.TASK, status=TaskStatus.NOT_STARTED.value)
        )
        repo.add(GtdItem(title="PJ", tag=Tag.PROJECT))
        assert len(repo.get_by_tag(Tag.TASK)) == 1

    def test_get_tasks(self, test_session):
        repo = DbGtdRepository(test_session)
        repo.add(GtdItem(title="未タスク"))
        repo.add(
            GtdItem(title="タスク", tag=Tag.TASK, status=TaskStatus.NOT_STARTED.value)
        )
        assert len(repo.get_tasks()) == 1

    def test_roundtrip_with_all_fields(self, test_session):
        from study_python.gtd.models import EnergyLevel, Location, TimeEstimate

        repo = DbGtdRepository(test_session)
        item = GtdItem(
            title="完全",
            item_status=ItemStatus.INBOX,
            tag=Tag.TASK,
            status=TaskStatus.IN_PROGRESS.value,
            locations=[Location.DESK, Location.HOME],
            time_estimate=TimeEstimate.WITHIN_30MIN,
            energy=EnergyLevel.HIGH,
            parent_project_id="proj-abc",
            parent_project_title="親PJ",
            order=1,
            note="メモ",
            deleted_at="",
        )
        repo.add(item)
        repo.flush_to_db()
        test_session.commit()

        repo2 = DbGtdRepository(test_session)
        loaded = repo2.items[0]
        assert loaded.title == "完全"
        assert loaded.tag == Tag.TASK
        assert loaded.locations == [Location.DESK, Location.HOME]
        assert loaded.time_estimate == TimeEstimate.WITHIN_30MIN
        assert loaded.energy == EnergyLevel.HIGH
        assert loaded.parent_project_id == "proj-abc"
        assert loaded.parent_project_title == "親PJ"
        assert loaded.order == 1
        assert loaded.note == "メモ"
