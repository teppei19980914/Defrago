"""実行ルーターのテスト."""

from study_python.gtd.models import GtdItem, Tag, TaskStatus
from study_python.gtd.web.routers.execution import _sort_tasks_by_project


class TestSortTasksByProject:
    """プロジェクトグルーピング・ソートのテスト."""

    def test_no_project_tasks_unchanged(self):
        """プロジェクト派生なしの場合、そのまま返す."""
        tasks = [
            GtdItem(title="A", tag=Tag.TASK, status=TaskStatus.NOT_STARTED),
            GtdItem(title="B", tag=Tag.TASK, status=TaskStatus.NOT_STARTED),
        ]
        result = _sort_tasks_by_project(tasks)
        assert [t.title for t in result] == ["A", "B"]

    def test_project_tasks_grouped_and_sorted(self):
        """プロジェクト派生タスクがグループ化・order順にソートされる."""
        tasks = [
            GtdItem(title="standalone", tag=Tag.TASK, status=TaskStatus.NOT_STARTED),
            GtdItem(
                title="sub2",
                tag=Tag.TASK,
                status=TaskStatus.NOT_STARTED,
                parent_project_id="proj1",
                parent_project_title="Project A",
                order=1,
            ),
            GtdItem(
                title="sub1",
                tag=Tag.TASK,
                status=TaskStatus.NOT_STARTED,
                parent_project_id="proj1",
                parent_project_title="Project A",
                order=0,
            ),
        ]
        result = _sort_tasks_by_project(tasks)
        assert [t.title for t in result] == ["standalone", "sub1", "sub2"]

    def test_empty_list(self):
        """空リストの場合、空リストを返す."""
        assert _sort_tasks_by_project([]) == []


class TestExecutionPage:
    """実行ページのテスト."""

    def test_execution_page_renders(self, client):
        """実行ページが正常に表示される."""
        response = client.get("/execution")
        assert response.status_code == 200
        assert "実行" in response.text
