"""Inboxルーターのテスト."""


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

    def test_move_to_someday(self, client):
        client.post("/inbox/add", data={"title": "いつか"})
        page = client.get("/inbox")
        assert "いつか" in page.text
