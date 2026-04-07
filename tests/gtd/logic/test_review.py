"""見直しロジックのテスト."""

import pytest

from study_python.gtd.logic.review import ReviewLogic
from study_python.gtd.models import (
    GtdItem,
    ItemStatus,
    Tag,
    TaskStatus,
)
from study_python.gtd.web.db_repository import DbGtdRepository


@pytest.fixture
def logic(repo: DbGtdRepository) -> ReviewLogic:
    return ReviewLogic(repo)


def _create_task(
    repo: DbGtdRepository,
    title: str = "テスト",
    tag: Tag = Tag.TASK,
    status: str | None = None,
) -> GtdItem:
    """テスト用タスクを作成する."""
    if status is None and tag != Tag.PROJECT:
        status = TaskStatus.NOT_STARTED.value
    item = GtdItem(
        title=title,
        item_status=ItemStatus.SOMEDAY,
        tag=tag,
        status=status,
    )
    repo.add(item)
    return item


class TestReviewLogic:
    """ReviewLogicのテスト."""

    def test_get_review_items_completed(
        self, logic: ReviewLogic, repo: DbGtdRepository
    ):
        _create_task(repo, "完了", status=TaskStatus.DONE.value)
        _create_task(repo, "未完了")

        review_items = logic.get_review_items()
        assert len(review_items) == 1
        assert review_items[0].title == "完了"

    def test_get_review_items_project(self, logic: ReviewLogic, repo: DbGtdRepository):
        _create_task(repo, "プロジェクト", tag=Tag.PROJECT)

        review_items = logic.get_review_items()
        assert len(review_items) == 1
        assert review_items[0].title == "プロジェクト"

    def test_get_review_items_both(self, logic: ReviewLogic, repo: DbGtdRepository):
        _create_task(repo, "完了", status=TaskStatus.DONE.value)
        _create_task(repo, "プロジェクト", tag=Tag.PROJECT)
        _create_task(repo, "未完了")

        review_items = logic.get_review_items()
        assert len(review_items) == 2

    def test_delete_item(self, logic: ReviewLogic, repo: DbGtdRepository):
        item = _create_task(repo, "削除対象", status=TaskStatus.DONE.value)
        result = logic.delete_item(item.id)
        assert result is not None
        assert result.title == "削除対象"
        assert len(repo.items) == 0

    def test_delete_item_nonexistent(self, logic: ReviewLogic):
        result = logic.delete_item("nonexistent")
        assert result is None

    def test_move_to_inbox(self, logic: ReviewLogic, repo: DbGtdRepository):
        item = _create_task(repo, "Inboxに戻す", status=TaskStatus.DONE.value)

        result = logic.move_to_inbox(item.id)
        assert result is not None
        assert result.item_status == ItemStatus.INBOX
        assert result.tag is None
        assert result.status is None
        assert result.locations == []
        assert result.time_estimate is None
        assert result.energy is None

    def test_move_to_inbox_nonexistent(self, logic: ReviewLogic):
        result = logic.move_to_inbox("nonexistent")
        assert result is None

    def test_get_completed_count(self, logic: ReviewLogic, repo: DbGtdRepository):
        _create_task(repo, "完了1", status=TaskStatus.DONE.value)
        _create_task(repo, "完了2", status=TaskStatus.DONE.value)
        _create_task(repo, "未完了")

        assert logic.get_completed_count() == 2

    def test_get_completed_count_zero(self, logic: ReviewLogic):
        assert logic.get_completed_count() == 0

    def test_get_project_count(self, logic: ReviewLogic, repo: DbGtdRepository):
        _create_task(repo, "PJ1", tag=Tag.PROJECT)
        _create_task(repo, "PJ2", tag=Tag.PROJECT)
        _create_task(repo, "タスク")

        assert logic.get_project_count() == 2

    def test_get_project_count_zero(self, logic: ReviewLogic):
        assert logic.get_project_count() == 0

    def test_decompose_project_success(self, logic: ReviewLogic, repo: DbGtdRepository):
        project = _create_task(repo, "大きなプロジェクト", tag=Tag.PROJECT)
        titles = ["サブタスク1", "サブタスク2", "サブタスク3"]

        result = logic.decompose_project(project.id, titles)

        assert len(result) == 3
        assert [item.title for item in result] == titles
        # 元のプロジェクトは削除されている
        assert repo.get(project.id) is None
        # 新しいアイテムがリポジトリに存在する
        assert len(repo.items) == 3

    def test_decompose_project_subtask_properties(
        self, logic: ReviewLogic, repo: DbGtdRepository
    ):
        project = _create_task(repo, "PJ", tag=Tag.PROJECT)
        result = logic.decompose_project(project.id, ["タスクA"])

        sub = result[0]
        assert sub.item_status == ItemStatus.INBOX
        assert sub.tag is None
        assert sub.status is None

    def test_decompose_project_item_not_found(self, logic: ReviewLogic):
        with pytest.raises(ValueError, match="Item not found"):
            logic.decompose_project("nonexistent", ["タスク"])

    def test_decompose_project_not_a_project(
        self, logic: ReviewLogic, repo: DbGtdRepository
    ):
        task = _create_task(repo, "普通のタスク", tag=Tag.TASK)
        with pytest.raises(ValueError, match="not a project"):
            logic.decompose_project(task.id, ["タスク"])

    def test_decompose_project_empty_titles(
        self, logic: ReviewLogic, repo: DbGtdRepository
    ):
        project = _create_task(repo, "PJ", tag=Tag.PROJECT)
        with pytest.raises(ValueError, match="At least one sub-task"):
            logic.decompose_project(project.id, [])

    def test_decompose_project_sets_parent_project_id(
        self, logic: ReviewLogic, repo: DbGtdRepository
    ):
        project = _create_task(repo, "大きなPJ", tag=Tag.PROJECT)
        project_id = project.id
        result = logic.decompose_project(project_id, ["タスクA", "タスクB"])

        assert result[0].parent_project_id == project_id
        assert result[1].parent_project_id == project_id
        assert result[0].parent_project_title == "大きなPJ"
        assert result[1].parent_project_title == "大きなPJ"

    def test_decompose_project_sets_order(
        self, logic: ReviewLogic, repo: DbGtdRepository
    ):
        project = _create_task(repo, "PJ", tag=Tag.PROJECT)
        result = logic.decompose_project(project.id, ["A", "B", "C"])

        assert result[0].order == 0
        assert result[1].order == 1
        assert result[2].order == 2

    # --- プロジェクト計画ウィザード ---

    def test_save_project_plan(self, logic: ReviewLogic, repo: DbGtdRepository):
        """目的・望ましい結果・サポート資料場所を保存できる."""
        project = _create_task(repo, "PJ", tag=Tag.PROJECT)
        result = logic.save_project_plan(
            project.id,
            purpose="効率化",
            outcome="処理時間50%短縮",
            support_location="Google Drive",
        )
        assert result is not None
        assert result.project_purpose == "効率化"
        assert result.project_outcome == "処理時間50%短縮"
        assert result.project_support_location == "Google Drive"

    def test_save_project_plan_non_project_returns_none(
        self, logic: ReviewLogic, repo: DbGtdRepository
    ):
        """プロジェクト以外には保存できない."""
        task = _create_task(repo, "タスク", tag=Tag.TASK)
        result = logic.save_project_plan(task.id, purpose="テスト")
        assert result is None

    def test_decompose_project_planned(self, logic: ReviewLogic, repo: DbGtdRepository):
        """計画済みプロジェクトを構造化サブタスクに分解できる."""
        project = _create_task(repo, "計画PJ", tag=Tag.PROJECT)
        project.project_purpose = "目的テスト"
        project.project_outcome = "結果テスト"
        project_id = project.id

        sub_tasks = [
            {"title": "調査", "is_next_action": True, "deadline": "2026-04-10"},
            {"title": "実装", "is_next_action": False, "deadline": "2026-04-20"},
        ]
        result = logic.decompose_project_planned(project_id, sub_tasks)

        assert len(result) == 2
        assert result[0].title == "調査"
        assert result[0].is_next_action is True
        assert result[0].deadline == "2026-04-10"
        assert result[0].parent_project_id == project_id
        assert result[0].order == 0
        assert "【目的】目的テスト" in result[0].note
        assert "【望ましい結果】結果テスト" in result[0].note

        assert result[1].title == "実装"
        assert result[1].is_next_action is False
        assert result[1].order == 1

        # 元のプロジェクトは削除されている
        assert repo.get(project_id) is None

    def test_decompose_project_planned_empty_raises(
        self, logic: ReviewLogic, repo: DbGtdRepository
    ):
        """サブタスクが空の場合はエラー."""
        project = _create_task(repo, "PJ", tag=Tag.PROJECT)
        with pytest.raises(ValueError, match="At least one sub-task"):
            logic.decompose_project_planned(project.id, [])

    def test_decompose_project_planned_skips_blank_titles(
        self, logic: ReviewLogic, repo: DbGtdRepository
    ):
        """空タイトルのサブタスクはスキップされる."""
        project = _create_task(repo, "PJ", tag=Tag.PROJECT)
        sub_tasks = [
            {"title": "有効", "is_next_action": False, "deadline": ""},
            {"title": "  ", "is_next_action": False, "deadline": ""},
        ]
        result = logic.decompose_project_planned(project.id, sub_tasks)
        assert len(result) == 1
        assert result[0].title == "有効"

    def test_move_to_inbox_preserves_parent_project(
        self, logic: ReviewLogic, repo: DbGtdRepository
    ):
        """Inboxに戻してもプロジェクト紐づけは保持される."""
        item = _create_task(repo, "サブタスク", status=TaskStatus.DONE.value)
        item.parent_project_id = "proj-123"
        item.parent_project_title = "親PJ"
        item.order = 0

        result = logic.move_to_inbox(item.id)
        assert result is not None
        assert result.parent_project_id == "proj-123"
        assert result.parent_project_title == "親PJ"
        assert result.order == 0
