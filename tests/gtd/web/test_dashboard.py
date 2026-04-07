"""ダッシュボードのテスト."""


class TestDashboard:
    """ダッシュボードのテスト."""

    def test_dashboard_renders(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "ダッシュボード" in response.text

    def test_dashboard_shows_stats(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert "Inbox" in response.text
        assert "完了" in response.text

    def test_dashboard_shows_next_action_clear(self, client):
        """空の状態ではクリアメッセージが表示される."""
        response = client.get("/")
        assert response.status_code == 200
        assert "クリア" in response.text

    def test_dashboard_guides_to_clarification_when_unclassified(self, client):
        """未分類のInboxアイテムがあれば明確化フェーズへ誘導."""
        client.post("/inbox/add", data={"title": "テスト"})
        response = client.get("/", follow_redirects=True)
        assert "明確化する" in response.text

    def test_dashboard_guides_to_execution_when_classified(self, client):
        """分類済みアイテムがあれば実行フェーズへ誘導."""
        client.post("/inbox/add", data={"title": "即実行タスク", "tag": "do_now"})
        response = client.get("/", follow_redirects=True)
        assert "実行する" in response.text
