"""明確化ロジックのテスト."""

import pytest

from study_python.gtd.logic.clarification import ClarificationLogic
from study_python.gtd.models import (
    DelegationStatus,
    DoNowStatus,
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
def logic(repo: DbGtdRepository) -> ClarificationLogic:
    return ClarificationLogic(repo)


def _create_inbox_item(repo: DbGtdRepository, title: str = "テスト") -> GtdItem:
    """Inbox状態の未分類テストアイテムを作成する."""
    item = GtdItem(title=title, item_status=ItemStatus.INBOX)
    repo.add(item)
    return item


class TestClarificationLogic:
    """ClarificationLogicのテスト."""

    def test_get_pending_items(self, logic: ClarificationLogic, repo: DbGtdRepository):
        _create_inbox_item(repo, "未処理1")
        _create_inbox_item(repo, "未処理2")
        item3 = _create_inbox_item(repo, "処理済み")
        item3.tag = Tag.TASK

        pending = logic.get_pending_items()
        assert len(pending) == 2

    def test_get_pending_items_excludes_classified(
        self, logic: ClarificationLogic, repo: DbGtdRepository
    ):
        _create_inbox_item(repo, "未分類")
        item = _create_inbox_item(repo, "分類済み")
        item.tag = Tag.DO_NOW

        pending = logic.get_pending_items()
        assert len(pending) == 1
        assert pending[0].title == "未分類"

    def test_classify_as_delegation(
        self, logic: ClarificationLogic, repo: DbGtdRepository
    ):
        item = _create_inbox_item(repo)
        result = logic.classify_as_delegation(item.id)
        assert result is not None
        assert result.tag == Tag.DELEGATION
        assert result.status == DelegationStatus.NOT_STARTED.value

    def test_classify_as_delegation_nonexistent(self, logic: ClarificationLogic):
        result = logic.classify_as_delegation("nonexistent")
        assert result is None

    def test_classify_as_project(
        self, logic: ClarificationLogic, repo: DbGtdRepository
    ):
        item = _create_inbox_item(repo)
        result = logic.classify_as_project(item.id)
        assert result is not None
        assert result.tag == Tag.PROJECT
        assert result.status is None

    def test_classify_as_project_nonexistent(self, logic: ClarificationLogic):
        result = logic.classify_as_project("nonexistent")
        assert result is None

    def test_classify_as_do_now(self, logic: ClarificationLogic, repo: DbGtdRepository):
        item = _create_inbox_item(repo)
        result = logic.classify_as_do_now(item.id)
        assert result is not None
        assert result.tag == Tag.DO_NOW
        assert result.status == DoNowStatus.NOT_STARTED.value

    def test_classify_as_do_now_nonexistent(self, logic: ClarificationLogic):
        result = logic.classify_as_do_now("nonexistent")
        assert result is None

    def test_classify_as_task_basic(
        self, logic: ClarificationLogic, repo: DbGtdRepository
    ):
        item = _create_inbox_item(repo)
        result = logic.classify_as_task(item.id)
        assert result is not None
        assert result.tag == Tag.TASK
        assert result.status == TaskStatus.NOT_STARTED.value
        assert result.locations == []
        assert result.time_estimate is None
        assert result.energy is None

    def test_classify_as_task_nonexistent(self, logic: ClarificationLogic):
        result = logic.classify_as_task("nonexistent")
        assert result is None

    def test_update_task_context(
        self, logic: ClarificationLogic, repo: DbGtdRepository
    ):
        item = _create_inbox_item(repo)
        logic.classify_as_task(item.id)

        result = logic.update_task_context(
            item.id,
            locations=[Location.COMMUTE],
            time_estimate=TimeEstimate.WITHIN_10MIN,
            energy=EnergyLevel.LOW,
        )
        assert result is not None
        assert result.locations == [Location.COMMUTE]
        assert result.time_estimate == TimeEstimate.WITHIN_10MIN
        assert result.energy == EnergyLevel.LOW

    def test_update_task_context_partial(
        self, logic: ClarificationLogic, repo: DbGtdRepository
    ):
        item = _create_inbox_item(repo)
        logic.classify_as_task(item.id)
        logic.update_task_context(
            item.id, locations=[Location.DESK], energy=EnergyLevel.MEDIUM
        )

        result = logic.update_task_context(item.id, energy=EnergyLevel.HIGH)
        assert result is not None
        assert result.locations == [Location.DESK]
        assert result.energy == EnergyLevel.HIGH

    def test_update_task_context_nonexistent(self, logic: ClarificationLogic):
        result = logic.update_task_context("nonexistent")
        assert result is None

    def test_update_task_context_non_task_tag(
        self, logic: ClarificationLogic, repo: DbGtdRepository
    ):
        item = _create_inbox_item(repo)
        logic.classify_as_delegation(item.id)

        result = logic.update_task_context(item.id, locations=[Location.DESK])
        assert result is None
