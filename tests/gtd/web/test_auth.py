"""認証のテスト."""


class TestAuth:
    """認証のテスト."""

    def test_login_page_renders(self, anon_client):
        response = anon_client.get("/login", follow_redirects=False)
        assert response.status_code == 200
        assert "ログイン" in response.text

    def test_login_success(self, anon_client):
        import os

        import bcrypt

        password = "correct-password"
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        os.environ["ADMIN_PASSWORD_HASH"] = pw_hash
        from study_python.gtd.web.config import get_settings

        get_settings.cache_clear()

        response = anon_client.post(
            "/login",
            data={"username": "admin", "password": password},
        )
        assert response.status_code == 302
        assert response.headers["location"] == "/"

    def test_login_failure(self, anon_client):
        response = anon_client.post(
            "/login",
            data={"username": "admin", "password": "wrong"},
            follow_redirects=True,
        )
        assert response.status_code == 401
        assert "正しくありません" in response.text

    def test_logout(self, client):
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["location"]

    def test_unauthenticated_redirect(self, anon_client):
        response = anon_client.get("/inbox")
        assert response.status_code in (302, 303)
