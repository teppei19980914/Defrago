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
