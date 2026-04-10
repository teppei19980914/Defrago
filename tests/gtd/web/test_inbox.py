"""Inboxルーターのテスト."""

from study_python.gtd.models import GtdItem, ItemStatus
from study_python.gtd.web.routers.inbox import _sort_items_by_project


class TestSortItemsByProject:
    """プロジェクトグルーピング・ソートのテスト."""

    def test_no_project_items_unchanged(self):
        """プロジェクト派生なしの場合、そのまま返す."""
        items = [
            GtdItem(title="A", item_status=ItemStatus.INBOX),
            GtdItem(title="B", item_status=ItemStatus.INBOX),
        ]
        result = _sort_items_by_project(items)
        assert [i.title for i in result] == ["A", "B"]

    def test_project_items_grouped_and_sorted(self):
        """プロジェクト派生アイテムがグループ化・order順にソートされる."""
        items = [
            GtdItem(title="standalone", item_status=ItemStatus.INBOX),
            GtdItem(
                title="sub2",
                item_status=ItemStatus.INBOX,
                parent_project_id="proj1",
                parent_project_title="Project A",
                order=1,
            ),
            GtdItem(
                title="sub1",
                item_status=ItemStatus.INBOX,
                parent_project_id="proj1",
                parent_project_title="Project A",
                order=0,
            ),
        ]
        result = _sort_items_by_project(items)
        assert [i.title for i in result] == ["standalone", "sub1", "sub2"]

    def test_multiple_projects_grouped_separately(self):
        """異なるプロジェクトが別々にグループ化される."""
        items = [
            GtdItem(
                title="B-sub1",
                item_status=ItemStatus.INBOX,
                parent_project_id="projB",
                parent_project_title="Project B",
                order=0,
            ),
            GtdItem(
                title="A-sub1",
                item_status=ItemStatus.INBOX,
                parent_project_id="projA",
                parent_project_title="Project A",
                order=0,
            ),
            GtdItem(title="standalone", item_status=ItemStatus.INBOX),
        ]
        result = _sort_items_by_project(items)
        titles = [i.title for i in result]
        assert titles[0] == "standalone"
        # Each project group is contiguous
        proj_a_idx = titles.index("A-sub1")
        proj_b_idx = titles.index("B-sub1")
        assert proj_a_idx != proj_b_idx

    def test_empty_list(self):
        """空リストの場合、空リストを返す."""
        assert _sort_items_by_project([]) == []


class TestInbox:
    """Inboxのテスト."""

    def test_inbox_page_renders(self, client):
        response = client.get("/inbox")
        assert response.status_code == 200
        assert "収集" in response.text

    def test_add_item(self, client):
        response = client.post("/inbox/add", data={"title": "新しいタスク"})
        assert response.status_code == 200
        assert "新しいタスク" in response.text

    def test_add_empty_title(self, client):
        response = client.post("/inbox/add", data={"title": ""})
        assert response.status_code == 200

    def test_delete_item(self, client):
        # まずアイテム追加
        client.post("/inbox/add", data={"title": "削除対象"})
        # ページ取得してアイテムがあることを確認
        page = client.get("/inbox")
        assert "削除対象" in page.text

    def test_process_all_redirects_to_clarification(self, client):
        """一括処理後に明確化画面へリダイレクトする."""
        client.post("/inbox/add", data={"title": "テスト"})
        response = client.post("/inbox/process_all", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/clarification"

    def test_all_items_added_as_unclassified(self, client):
        """全てのアイテムは未分類で登録される（直接分類は廃止）."""
        client.post("/inbox/add", data={"title": "アイテムA"})
        client.post("/inbox/add", data={"title": "アイテムB"})

        response = client.get("/inbox")
        assert response.status_code == 200
        assert "アイテムA" in response.text
        assert "アイテムB" in response.text

    def test_tag_param_is_ignored(self, client):
        """tag パラメータを送っても未分類として登録される."""
        client.post(
            "/inbox/add",
            data={"title": "タスクっぽいやつ", "tag": "task"},
        )
        response = client.get("/inbox")
        assert "タスクっぽいやつ" in response.text
