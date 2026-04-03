"""認証のテスト."""

from study_python.gtd.web.auth import register_user


class TestAuth:
    """認証のテスト."""

    def test_login_page_renders(self, anon_client):
        response = anon_client.get("/login", follow_redirects=False)
        assert response.status_code == 200
        assert "ログイン" in response.text

    def test_login_success(self, anon_client, test_session):
        register_user(test_session, "loginuser", "correct-password")
        test_session.commit()

        response = anon_client.post(
            "/login",
            data={"username": "loginuser", "password": "correct-password"},
        )
        assert response.status_code == 302
        assert response.headers["location"] == "/"

    def test_login_failure(self, anon_client):
        response = anon_client.post(
            "/login",
            data={"username": "nobody", "password": "wrong"},
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

    def test_register_page_renders(self, anon_client):
        response = anon_client.get("/register", follow_redirects=False)
        assert response.status_code == 200
        assert "新規登録" in response.text

    def test_register_success(self, anon_client):
        response = anon_client.post(
            "/register",
            data={
                "username": "newuser",
                "password": "secure-password",
                "password_confirm": "secure-password",
            },
        )
        assert response.status_code == 302
        assert response.headers["location"] == "/"

    def test_register_short_password(self, anon_client):
        response = anon_client.post(
            "/register",
            data={
                "username": "newuser",
                "password": "short",
                "password_confirm": "short",
            },
            follow_redirects=True,
        )
        assert "8文字以上" in response.text

    def test_register_password_mismatch(self, anon_client):
        response = anon_client.post(
            "/register",
            data={
                "username": "newuser",
                "password": "password1234",
                "password_confirm": "different1234",
            },
            follow_redirects=True,
        )
        assert "一致しません" in response.text

    def test_register_duplicate_username(self, anon_client, test_session):
        register_user(test_session, "existing", "password1234")
        test_session.commit()

        response = anon_client.post(
            "/register",
            data={
                "username": "existing",
                "password": "password1234",
                "password_confirm": "password1234",
            },
            follow_redirects=True,
        )
        assert "既に使用されています" in response.text
