"""明確化ロジックのテスト."""

from pathlib import Path

import pytest

from study_python.gtd.logic.clarification import ClarificationLogic
from study_python.gtd.models import (
    CalendarStatus,
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
from study_python.gtd.repository import GtdRepository


@pytest.fixture
def repo(tmp_path: Path) -> GtdRepository:
    return GtdRepository(data_path=tmp_path / "test.json")


@pytest.fixture
def logic(repo: GtdRepository) -> ClarificationLogic:
    return ClarificationLogic(repo)


def _create_someday_item(repo: GtdRepository, title: str = "テスト") -> GtdItem:
    """いつかやるステータスのテストアイテムを作成する."""
    item = GtdItem(title=title, item_status=ItemStatus.SOMEDAY)
    repo.add(item)
    return item


class TestClarificationLogic:
    """ClarificationLogicのテスト."""

    def test_get_pending_items(self, logic: ClarificationLogic, repo: GtdRepository):
        _create_someday_item(repo, "未処理1")
        _create_someday_item(repo, "未処理2")
        item3 = _create_someday_item(repo, "処理済み")
        item3.tag = Tag.TASK  # タグが設定済み

        pending = logic.get_pending_items()
        assert len(pending) == 2

    def test_get_pending_items_excludes_inbox(
        self, logic: ClarificationLogic, repo: GtdRepository
    ):
        repo.add(GtdItem(title="Inbox", item_status=ItemStatus.INBOX))
        _create_someday_item(repo, "Someday")

        pending = logic.get_pending_items()
        assert len(pending) == 1

    def test_classify_as_delegation(
        self, logic: ClarificationLogic, repo: GtdRepository
    ):
        item = _create_someday_item(repo)
        result = logic.classify_as_delegation(item.id)
        assert result is not None
        assert result.tag == Tag.DELEGATION
        assert result.status == DelegationStatus.NOT_STARTED.value

    def test_classify_as_delegation_nonexistent(self, logic: ClarificationLogic):
        result = logic.classify_as_delegation("nonexistent")
        assert result is None

    def test_classify_as_calendar(self, logic: ClarificationLogic, repo: GtdRepository):
        item = _create_someday_item(repo)
        result = logic.classify_as_calendar(item.id)
        assert result is not None
        assert result.tag == Tag.CALENDAR
        assert result.status == CalendarStatus.NOT_STARTED.value

    def test_classify_as_calendar_nonexistent(self, logic: ClarificationLogic):
        result = logic.classify_as_calendar("nonexistent")
        assert result is None

    def test_classify_as_project(self, logic: ClarificationLogic, repo: GtdRepository):
        item = _create_someday_item(repo)
        result = logic.classify_as_project(item.id)
        assert result is not None
        assert result.tag == Tag.PROJECT
        assert result.status is None

    def test_classify_as_project_nonexistent(self, logic: ClarificationLogic):
        result = logic.classify_as_project("nonexistent")
        assert result is None

    def test_classify_as_do_now(self, logic: ClarificationLogic, repo: GtdRepository):
        item = _create_someday_item(repo)
        result = logic.classify_as_do_now(item.id)
        assert result is not None
        assert result.tag == Tag.DO_NOW
        assert result.status == DoNowStatus.NOT_STARTED.value

    def test_classify_as_do_now_nonexistent(self, logic: ClarificationLogic):
        result = logic.classify_as_do_now("nonexistent")
        assert result is None

    def test_classify_as_task_basic(
        self, logic: ClarificationLogic, repo: GtdRepository
    ):
        item = _create_someday_item(repo)
        result = logic.classify_as_task(
            item.id,
            locations=[Location.DESK],
            time_estimate=TimeEstimate.WITHIN_30MIN,
            energy=EnergyLevel.MEDIUM,
        )
        assert result is not None
        assert result.tag == Tag.TASK
        assert result.status == TaskStatus.NOT_STARTED.value
        assert result.locations == [Location.DESK]
        assert result.time_estimate == TimeEstimate.WITHIN_30MIN
        assert result.energy == EnergyLevel.MEDIUM

    def test_classify_as_task_with_context(
        self, logic: ClarificationLogic, repo: GtdRepository
    ):
        item = _create_someday_item(repo)
        result = logic.classify_as_task(
            item.id,
            locations=[Location.DESK, Location.HOME],
            time_estimate=TimeEstimate.WITHIN_30MIN,
            energy=EnergyLevel.HIGH,
        )
        assert result is not None
        assert result.locations == [Location.DESK, Location.HOME]
        assert result.time_estimate == TimeEstimate.WITHIN_30MIN
        assert result.energy == EnergyLevel.HIGH

    def test_classify_as_task_nonexistent(self, logic: ClarificationLogic):
        result = logic.classify_as_task(
            "nonexistent",
            locations=[Location.DESK],
            time_estimate=TimeEstimate.WITHIN_30MIN,
            energy=EnergyLevel.MEDIUM,
        )
        assert result is None

    def test_classify_as_task_empty_locations(
        self, logic: ClarificationLogic, repo: GtdRepository
    ):
        item = _create_someday_item(repo)
        with pytest.raises(ValueError, match="At least one location"):
            logic.classify_as_task(
                item.id,
                locations=[],
                time_estimate=TimeEstimate.WITHIN_30MIN,
                energy=EnergyLevel.MEDIUM,
            )

    def test_update_task_context(self, logic: ClarificationLogic, repo: GtdRepository):
        item = _create_someday_item(repo)
        logic.classify_as_task(
            item.id,
            locations=[Location.DESK],
            time_estimate=TimeEstimate.WITHIN_30MIN,
            energy=EnergyLevel.MEDIUM,
        )

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
        self, logic: ClarificationLogic, repo: GtdRepository
    ):
        item = _create_someday_item(repo)
        logic.classify_as_task(
            item.id,
            locations=[Location.DESK],
            time_estimate=TimeEstimate.WITHIN_30MIN,
            energy=EnergyLevel.MEDIUM,
        )

        result = logic.update_task_context(item.id, energy=EnergyLevel.HIGH)
        assert result is not None
        assert result.locations == [Location.DESK]  # 変更なし
        assert result.time_estimate == TimeEstimate.WITHIN_30MIN  # 変更なし
        assert result.energy == EnergyLevel.HIGH  # 更新された

    def test_update_task_context_nonexistent(self, logic: ClarificationLogic):
        result = logic.update_task_context("nonexistent")
        assert result is None

    def test_update_task_context_non_task_tag(
        self, logic: ClarificationLogic, repo: GtdRepository
    ):
        item = _create_someday_item(repo)
        logic.classify_as_delegation(item.id)

        result = logic.update_task_context(item.id, locations=[Location.DESK])
        assert result is None
