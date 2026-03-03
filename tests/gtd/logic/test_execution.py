"""実行ロジックのテスト."""

from pathlib import Path

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
from study_python.gtd.repository import GtdRepository


@pytest.fixture
def repo(tmp_path: Path) -> GtdRepository:
    return GtdRepository(data_path=tmp_path / "test.json")


@pytest.fixture
def logic(repo: GtdRepository) -> ExecutionLogic:
    return ExecutionLogic(repo)


def _create_task(
    repo: GtdRepository,
    title: str = "テスト",
    tag: Tag = Tag.TASK,
    status: str | None = None,
) -> GtdItem:
    """テスト用タスクを作成する."""
    if status is None and tag != Tag.PROJECT:
        status = TaskStatus.NOT_STARTED.value if tag == Tag.TASK else "not_started"
    item = GtdItem(
        title=title,
        item_status=ItemStatus.SOMEDAY,
        tag=tag,
        status=status,
    )
    repo.add(item)
    return item


class TestExecutionLogic:
    """ExecutionLogicのテスト."""

    def test_get_active_tasks(self, logic: ExecutionLogic, repo: GtdRepository):
        _create_task(repo, "未着手")
        _create_task(repo, "完了", status=TaskStatus.DONE.value)
        _create_task(repo, "プロジェクト", tag=Tag.PROJECT)

        active = logic.get_active_tasks()
        assert len(active) == 1
        assert active[0].title == "未着手"

    def test_get_active_tasks_includes_multiple_tags(
        self, logic: ExecutionLogic, repo: GtdRepository
    ):
        _create_task(repo, "タスク", tag=Tag.TASK)
        _create_task(repo, "依頼", tag=Tag.DELEGATION)
        _create_task(repo, "即実行", tag=Tag.DO_NOW)
        _create_task(repo, "カレンダー", tag=Tag.CALENDAR)

        active = logic.get_active_tasks()
        assert len(active) == 4

    def test_update_status_task(self, logic: ExecutionLogic, repo: GtdRepository):
        item = _create_task(repo)
        result = logic.update_status(item.id, TaskStatus.IN_PROGRESS.value)
        assert result is not None
        assert result.status == TaskStatus.IN_PROGRESS.value

    def test_update_status_to_done(self, logic: ExecutionLogic, repo: GtdRepository):
        item = _create_task(repo)
        result = logic.update_status(item.id, TaskStatus.DONE.value)
        assert result is not None
        assert result.status == TaskStatus.DONE.value

    def test_update_status_delegation(self, logic: ExecutionLogic, repo: GtdRepository):
        item = _create_task(repo, tag=Tag.DELEGATION)
        result = logic.update_status(item.id, DelegationStatus.WAITING.value)
        assert result is not None
        assert result.status == DelegationStatus.WAITING.value

    def test_update_status_do_now(self, logic: ExecutionLogic, repo: GtdRepository):
        item = _create_task(repo, tag=Tag.DO_NOW)
        result = logic.update_status(item.id, DoNowStatus.DONE.value)
        assert result is not None
        assert result.status == DoNowStatus.DONE.value

    def test_update_status_invalid_value(
        self, logic: ExecutionLogic, repo: GtdRepository
    ):
        item = _create_task(repo)
        with pytest.raises(ValueError, match="無効なステータスです"):
            logic.update_status(item.id, "invalid_status")

    def test_update_status_nonexistent(self, logic: ExecutionLogic):
        result = logic.update_status("nonexistent", TaskStatus.DONE.value)
        assert result is None

    def test_update_status_on_project(self, logic: ExecutionLogic, repo: GtdRepository):
        item = _create_task(repo, tag=Tag.PROJECT)
        result = logic.update_status(item.id, "done")
        assert result is None

    def test_update_status_on_non_task(
        self, logic: ExecutionLogic, repo: GtdRepository
    ):
        item = GtdItem(title="未タスク")
        repo.add(item)
        result = logic.update_status(item.id, "done")
        assert result is None

    def test_get_available_statuses_task(
        self, logic: ExecutionLogic, repo: GtdRepository
    ):
        item = _create_task(repo, tag=Tag.TASK)
        statuses = logic.get_available_statuses(item.id)
        assert statuses is not None
        assert "not_started" in statuses
        assert "in_progress" in statuses
        assert "done" in statuses

    def test_get_available_statuses_delegation(
        self, logic: ExecutionLogic, repo: GtdRepository
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
        self, logic: ExecutionLogic, repo: GtdRepository
    ):
        item = _create_task(repo, tag=Tag.PROJECT)
        statuses = logic.get_available_statuses(item.id)
        assert statuses is None

    def test_get_available_statuses_non_task(
        self, logic: ExecutionLogic, repo: GtdRepository
    ):
        item = GtdItem(title="未タスク")
        repo.add(item)
        statuses = logic.get_available_statuses(item.id)
        assert statuses is None
