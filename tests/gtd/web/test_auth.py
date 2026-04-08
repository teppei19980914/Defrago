"""認証のテスト."""

from study_python.gtd.web.auth import register_user
from study_python.gtd.web.db_models import GtdItemRow, NotificationRow, UserRow


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


class TestAccountDeletion:
    """アカウント物理削除機能 (#6) のテスト."""

    def test_delete_account_requires_confirm(self, client, test_session):
        """confirm=yes がないと削除されず設定画面にリダイレクトする."""
        response = client.post(
            "/settings/delete_account",
            data={},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/settings"
        # ユーザー行が残存していること
        assert test_session.query(UserRow).filter_by(username="testuser").count() == 1

    def test_delete_account_removes_user_and_data(self, client, test_session):
        """confirm=yes でユーザーと関連データがすべて物理削除される."""
        # 事前にアイテムを1件追加
        client.post("/inbox/add", data={"title": "削除対象アイテム"})
        user = test_session.query(UserRow).filter_by(username="testuser").one()
        user_id = user.id
        assert test_session.query(GtdItemRow).filter_by(user_id=user_id).count() >= 1

        response = client.post(
            "/settings/delete_account",
            data={"confirm": "yes"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

        # ユーザー・アイテム・通知がDBから完全に消えていること
        test_session.expire_all()
        assert test_session.query(UserRow).filter_by(id=user_id).count() == 0
        assert test_session.query(GtdItemRow).filter_by(user_id=user_id).count() == 0
        assert (
            test_session.query(NotificationRow).filter_by(user_id=user_id).count() == 0
        )

    def test_delete_account_requires_auth(self, anon_client):
        """未認証ユーザーは削除エンドポイントにアクセスできない."""
        response = anon_client.post(
            "/settings/delete_account",
            data={"confirm": "yes"},
            follow_redirects=False,
        )
        assert response.status_code in (302, 303)
        assert "/login" in response.headers["location"]

    def test_delete_account_does_not_affect_other_users(
        self, client, anon_client, test_session
    ):
        """他ユーザーのデータは削除されない."""
        # 別ユーザーを登録＋アイテムも追加
        register_user(test_session, "otheruser", "password1234")
        test_session.commit()
        anon_client.post(
            "/login",
            data={"username": "otheruser", "password": "password1234"},
        )
        anon_client.post("/inbox/add", data={"title": "他ユーザーのアイテム"})

        other = test_session.query(UserRow).filter_by(username="otheruser").one()
        other_id = other.id
        test_session.expire_all()
        assert test_session.query(GtdItemRow).filter_by(user_id=other_id).count() >= 1

        # testuser がアカウント削除
        client.post("/settings/delete_account", data={"confirm": "yes"})

        # otheruser のデータは健在
        test_session.expire_all()
        assert test_session.query(UserRow).filter_by(id=other_id).count() == 1
        assert test_session.query(GtdItemRow).filter_by(user_id=other_id).count() >= 1
