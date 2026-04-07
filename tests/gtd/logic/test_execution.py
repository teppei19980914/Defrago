"""実行ロジックのテスト."""

import pytest

from study_python.gtd.logic.execution import ExecutionLogic
from study_python.gtd.models import (
    DelegationStatus,
    DoNowStatus,
    GtdItem,
    ItemStatus,
    Tag,
    TaskStatus,
)
from study_python.gtd.web.db_repository import DbGtdRepository


@pytest.fixture
def logic(repo: DbGtdRepository) -> ExecutionLogic:
    return ExecutionLogic(repo)


def _create_task(
    repo: DbGtdRepository,
    title: str = "テスト",
    tag: Tag = Tag.TASK,
    status: str | None = None,
) -> GtdItem:
    """テスト用タスクを作成する."""
    if status is None and tag != Tag.PROJECT:
        status = TaskStatus.NOT_STARTED.value if tag == Tag.TASK else "not_started"
    item = GtdItem(
        title=title,
        item_status=ItemStatus.INBOX,
        tag=tag,
        status=status,
    )
    repo.add(item)
    return item


class TestExecutionLogic:
    """ExecutionLogicのテスト."""

    def test_get_active_tasks(self, logic: ExecutionLogic, repo: DbGtdRepository):
        _create_task(repo, "未着手")
        _create_task(repo, "完了", status=TaskStatus.DONE.value)
        _create_task(repo, "プロジェクト", tag=Tag.PROJECT)

        active = logic.get_active_tasks()
        assert len(active) == 1
        assert active[0].title == "未着手"

    def test_get_active_tasks_includes_3_tags(
        self, logic: ExecutionLogic, repo: DbGtdRepository
    ):
        _create_task(repo, "タスク", tag=Tag.TASK)
        _create_task(repo, "委任", tag=Tag.DELEGATION)
        _create_task(repo, "即実行", tag=Tag.DO_NOW)

        active = logic.get_active_tasks()
        assert len(active) == 3

    def test_get_active_tasks_excludes_trash(
        self, logic: ExecutionLogic, repo: DbGtdRepository
    ):
        item = _create_task(repo, "ゴミ箱内")
        item.item_status = ItemStatus.TRASH

        active = logic.get_active_tasks()
        assert len(active) == 0

    def test_update_status_task(self, logic: ExecutionLogic, repo: DbGtdRepository):
        item = _create_task(repo)
        result = logic.update_status(item.id, TaskStatus.IN_PROGRESS.value)
        assert result is not None
        assert result.status == TaskStatus.IN_PROGRESS.value

    def test_update_status_to_done(self, logic: ExecutionLogic, repo: DbGtdRepository):
        item = _create_task(repo)
        result = logic.update_status(item.id, TaskStatus.DONE.value)
        assert result is not None
        assert result.status == TaskStatus.DONE.value

    def test_update_status_delegation(
        self, logic: ExecutionLogic, repo: DbGtdRepository
    ):
        item = _create_task(repo, tag=Tag.DELEGATION)
        result = logic.update_status(item.id, DelegationStatus.WAITING.value)
        assert result is not None
        assert result.status == DelegationStatus.WAITING.value

    def test_update_status_do_now(self, logic: ExecutionLogic, repo: DbGtdRepository):
        item = _create_task(repo, tag=Tag.DO_NOW)
        result = logic.update_status(item.id, DoNowStatus.DONE.value)
        assert result is not None
        assert result.status == DoNowStatus.DONE.value

    def test_update_status_invalid_value(
        self, logic: ExecutionLogic, repo: DbGtdRepository
    ):
        item = _create_task(repo)
        with pytest.raises(ValueError, match="無効なステータスです"):
            logic.update_status(item.id, "invalid_status")

    def test_update_status_nonexistent(self, logic: ExecutionLogic):
        result = logic.update_status("nonexistent", TaskStatus.DONE.value)
        assert result is None

    def test_update_status_on_project(
        self, logic: ExecutionLogic, repo: DbGtdRepository
    ):
        item = _create_task(repo, tag=Tag.PROJECT)
        result = logic.update_status(item.id, "done")
        assert result is None

    def test_update_status_on_non_task(
        self, logic: ExecutionLogic, repo: DbGtdRepository
    ):
        item = GtdItem(title="未タスク")
        repo.add(item)
        result = logic.update_status(item.id, "done")
        assert result is None

    def test_get_available_statuses_task(
        self, logic: ExecutionLogic, repo: DbGtdRepository
    ):
        item = _create_task(repo, tag=Tag.TASK)
        statuses = logic.get_available_statuses(item.id)
        assert statuses is not None
        assert "not_started" in statuses
        assert "in_progress" in statuses
        assert "done" in statuses

    def test_get_available_statuses_delegation(
        self, logic: ExecutionLogic, repo: DbGtdRepository
    ):
        item = _create_task(repo, tag=Tag.DELEGATION)
        statuses = logic.get_available_statuses(item.id)
        assert statuses is not None
        assert "not_started" in statuses
        assert "waiting" in statuses
        assert "done" in statuses

    def test_get_available_statuses_nonexistent(self, logic: ExecutionLogic):
        statuses = logic.get_available_statuses("nonexistent")
        assert statuses is None

    def test_get_available_statuses_project(
        self, logic: ExecutionLogic, repo: DbGtdRepository
    ):
        item = _create_task(repo, tag=Tag.PROJECT)
        statuses = logic.get_available_statuses(item.id)
        assert statuses is None

    def test_get_available_statuses_non_task(
        self, logic: ExecutionLogic, repo: DbGtdRepository
    ):
        item = GtdItem(title="未タスク")
        repo.add(item)
        statuses = logic.get_available_statuses(item.id)
        assert statuses is None


class TestReorderItem:
    """reorder_itemのテスト."""

    def _create_project_items(
        self, repo: DbGtdRepository, project_id: str = "proj-1"
    ) -> list[GtdItem]:
        items = []
        for i, title in enumerate(["A", "B", "C"]):
            item = GtdItem(
                title=title,
                tag=Tag.TASK,
                status=TaskStatus.NOT_STARTED.value,
                parent_project_id=project_id,
                parent_project_title="PJ",
                order=i,
            )
            repo.add(item)
            items.append(item)
        return items

    def test_reorder_up(self, logic: ExecutionLogic, repo: DbGtdRepository):
        items = self._create_project_items(repo)
        result = logic.reorder_item(items[1].id, "up")
        assert result is True
        assert items[1].order == 0
        assert items[0].order == 1

    def test_reorder_down(self, logic: ExecutionLogic, repo: DbGtdRepository):
        items = self._create_project_items(repo)
        result = logic.reorder_item(items[0].id, "down")
        assert result is True
        assert items[0].order == 1
        assert items[1].order == 0

    def test_reorder_no_parent_project(
        self, logic: ExecutionLogic, repo: DbGtdRepository
    ):
        item = GtdItem(title="通常", tag=Tag.TASK, status=TaskStatus.NOT_STARTED.value)
        repo.add(item)
        result = logic.reorder_item(item.id, "up")
        assert result is False
