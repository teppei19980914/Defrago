"""整理ロジックのテスト."""

from pathlib import Path

import pytest

from study_python.gtd.logic.organization import OrganizationLogic
from study_python.gtd.models import GtdItem, ItemStatus, Tag, TaskStatus
from study_python.gtd.repository import GtdRepository


@pytest.fixture
def repo(tmp_path: Path) -> GtdRepository:
    return GtdRepository(data_path=tmp_path / "test.json")


@pytest.fixture
def logic(repo: GtdRepository) -> OrganizationLogic:
    return OrganizationLogic(repo)


def _create_task(
    repo: GtdRepository,
    title: str = "テスト",
    tag: Tag = Tag.TASK,
    importance: int | None = None,
    urgency: int | None = None,
) -> GtdItem:
    """テスト用タスクを作成する."""
    item = GtdItem(
        title=title,
        item_status=ItemStatus.SOMEDAY,
        tag=tag,
        status=TaskStatus.NOT_STARTED.value if tag != Tag.PROJECT else None,
        importance=importance,
        urgency=urgency,
    )
    repo.add(item)
    return item


class TestOrganizationLogic:
    """OrganizationLogicのテスト."""

    def test_get_unorganized_tasks(self, logic: OrganizationLogic, repo: GtdRepository):
        _create_task(repo, "未整理1")
        _create_task(repo, "整理済み", importance=5, urgency=3)
        _create_task(repo, "未整理2")

        unorganized = logic.get_unorganized_tasks()
        assert len(unorganized) == 2

    def test_get_unorganized_tasks_excludes_projects(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        _create_task(repo, "プロジェクト", tag=Tag.PROJECT)
        _create_task(repo, "タスク")

        unorganized = logic.get_unorganized_tasks()
        assert len(unorganized) == 1
        assert unorganized[0].title == "タスク"

    def test_set_importance_urgency(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        item = _create_task(repo)
        result = logic.set_importance_urgency(item.id, 8, 3)
        assert result is not None
        assert result.importance == 8
        assert result.urgency == 3

    def test_set_importance_urgency_min_values(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        item = _create_task(repo)
        result = logic.set_importance_urgency(item.id, 1, 1)
        assert result is not None
        assert result.importance == 1
        assert result.urgency == 1

    def test_set_importance_urgency_max_values(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        item = _create_task(repo)
        result = logic.set_importance_urgency(item.id, 10, 10)
        assert result is not None
        assert result.importance == 10
        assert result.urgency == 10

    def test_set_importance_urgency_invalid_importance_low(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        item = _create_task(repo)
        with pytest.raises(ValueError, match="重要度"):
            logic.set_importance_urgency(item.id, 0, 5)

    def test_set_importance_urgency_invalid_importance_high(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        item = _create_task(repo)
        with pytest.raises(ValueError, match="重要度"):
            logic.set_importance_urgency(item.id, 11, 5)

    def test_set_importance_urgency_invalid_urgency_low(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        item = _create_task(repo)
        with pytest.raises(ValueError, match="緊急度"):
            logic.set_importance_urgency(item.id, 5, 0)

    def test_set_importance_urgency_invalid_urgency_high(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        item = _create_task(repo)
        with pytest.raises(ValueError, match="緊急度"):
            logic.set_importance_urgency(item.id, 5, 11)

    def test_set_importance_urgency_nonexistent(self, logic: OrganizationLogic):
        result = logic.set_importance_urgency("nonexistent", 5, 5)
        assert result is None

    def test_set_importance_urgency_on_project(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        item = _create_task(repo, tag=Tag.PROJECT)
        result = logic.set_importance_urgency(item.id, 5, 5)
        assert result is None

    def test_set_importance_urgency_on_non_task(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        item = GtdItem(title="未タスク")
        repo.add(item)
        result = logic.set_importance_urgency(item.id, 5, 5)
        assert result is None

    def test_get_matrix_quadrants(self, logic: OrganizationLogic, repo: GtdRepository):
        _create_task(repo, "Q1", importance=8, urgency=7)
        _create_task(repo, "Q2", importance=9, urgency=2)
        _create_task(repo, "Q3", importance=3, urgency=8)
        _create_task(repo, "Q4", importance=2, urgency=1)

        quadrants = logic.get_matrix_quadrants()
        assert len(quadrants["q1_urgent_important"]) == 1
        assert len(quadrants["q2_not_urgent_important"]) == 1
        assert len(quadrants["q3_urgent_not_important"]) == 1
        assert len(quadrants["q4_not_urgent_not_important"]) == 1

    def test_get_matrix_quadrants_excludes_unscored(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        _create_task(repo, "未評価")
        _create_task(repo, "評価済み", importance=5, urgency=5)

        quadrants = logic.get_matrix_quadrants()
        total = sum(len(v) for v in quadrants.values())
        assert total == 1

    def test_get_matrix_quadrants_excludes_projects(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        _create_task(repo, "プロジェクト", tag=Tag.PROJECT, importance=8, urgency=8)
        _create_task(repo, "タスク", importance=8, urgency=8)

        quadrants = logic.get_matrix_quadrants()
        assert len(quadrants["q1_urgent_important"]) == 1

    def test_get_matrix_quadrants_boundary_values(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        # importance=5, urgency=5 はQ4（境界値は<=5）
        _create_task(repo, "境界", importance=5, urgency=5)

        quadrants = logic.get_matrix_quadrants()
        assert len(quadrants["q4_not_urgent_not_important"]) == 1

    def test_get_matrix_quadrants_boundary_6(
        self, logic: OrganizationLogic, repo: GtdRepository
    ):
        # importance=6, urgency=6 はQ1
        _create_task(repo, "境界6", importance=6, urgency=6)

        quadrants = logic.get_matrix_quadrants()
        assert len(quadrants["q1_urgent_important"]) == 1
