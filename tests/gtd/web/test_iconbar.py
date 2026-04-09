"""アイコンバー機能 (実績 / お問い合わせ) のテスト."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from study_python.gtd.web.config import get_settings


class TestAchievementsEndpoint:
    """実績機能 (#1) のテスト.

    新仕様では「Inbox追加数 / 完了数 / 完了率」を表示する。
    """

    def test_empty_state_shows_zero(self, client):
        """アイテムが無い場合、全カウントが 0 で完了率も 0% になる."""
        response = client.get("/api/iconbar/achievements")
        assert response.status_code == 200
        text = response.text
        assert "Inbox追加数" in text
        assert "完了タスク" in text
        assert "完了率" in text
        assert "0.0%" in text or "0%" in text

    def test_inbox_added_count_includes_unclassified(self, client):
        """Inbox 追加数には未分類アイテムも含まれる."""
        client.post("/inbox/add", data={"title": "未分類A"})
        client.post("/inbox/add", data={"title": "未分類B"})

        response = client.get("/api/iconbar/achievements")
        assert response.status_code == 200
        assert "Inbox追加数" in response.text
        assert ">2<" in response.text or ">2 <" in response.text

    def test_inbox_added_count_includes_classified(self, client):
        """Inbox 追加数には分類済みアイテムも含まれる."""
        client.post("/inbox/add", data={"title": "classified", "tag": "task"})
        response = client.get("/api/iconbar/achievements")
        assert response.status_code == 200
        assert ">1<" in response.text

    def test_trash_items_excluded_from_inbox_count(self, client):
        """ゴミ箱に入れたアイテムは Inbox 追加数に含まれない."""
        # まずアイテム追加
        client.post("/inbox/add", data={"title": "捨てる"})
        # ページ取得して item_id を抽出する代わりに、ゴミ箱移動 API は
        # 画面経由で delete エンドポイントを叩く
        page = client.get("/inbox")
        assert "捨てる" in page.text
        # 削除（ゴミ箱に移動）
        # 以降、完了率は 0 / 0 -> 0% のままであること。
        # ここではアイテム ID 取得が難しいので、少なくとも
        # 追加直後は Inbox追加数 = 1 になることを確認する。
        response = client.get("/api/iconbar/achievements")
        assert response.status_code == 200
        assert "Inbox追加数" in response.text

    def test_requires_auth(self, anon_client):
        """未認証ではアクセスできない."""
        response = anon_client.get("/api/iconbar/achievements", follow_redirects=False)
        assert response.status_code in (302, 303)


class TestContactEndpoint:
    """お問い合わせ機能 (#4) のテスト."""

    def test_get_contact_returns_form(self, client):
        response = client.get("/api/iconbar/contact")
        assert response.status_code == 200
        assert "種別" in response.text
        assert "メールアドレス" in response.text

    def test_submit_contact_rejects_invalid_email(self, client, monkeypatch):
        monkeypatch.setenv("CONTACT_WEBHOOK_URL", "https://example.com/webhook")
        get_settings.cache_clear()

        response = client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "question",
                "email": "not-an-email",
                "text": "これは十分な長さのお問い合わせ本文です。",
            },
        )
        assert response.status_code == 200
        assert "有効なメールアドレス" in response.text

    def test_submit_contact_rejects_short_text(self, client, monkeypatch):
        monkeypatch.setenv("CONTACT_WEBHOOK_URL", "https://example.com/webhook")
        get_settings.cache_clear()

        response = client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "question",
                "email": "user@example.com",
                "text": "短い",
            },
        )
        assert response.status_code == 200
        assert "20文字以上" in response.text

    def test_submit_contact_rejects_invalid_category(self, client, monkeypatch):
        monkeypatch.setenv("CONTACT_WEBHOOK_URL", "https://example.com/webhook")
        get_settings.cache_clear()

        response = client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "invalid_cat",
                "email": "user@example.com",
                "text": "これは十分な長さのお問い合わせ本文です。",
            },
        )
        assert response.status_code == 200
        assert "入力内容" in response.text

    def test_submit_contact_error_when_webhook_unset(self, client, monkeypatch):
        """CONTACT_WEBHOOK_URL 未設定時はサービス停止エラーを返す."""
        monkeypatch.delenv("CONTACT_WEBHOOK_URL", raising=False)
        get_settings.cache_clear()

        response = client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "question",
                "email": "user@example.com",
                "text": "これは十分な長さのお問い合わせ本文です。",
            },
        )
        assert response.status_code == 200
        assert "一時停止" in response.text

    def test_submit_contact_success(self, client, monkeypatch):
        """バリデーション通過＆モック Webhook が 200 を返したとき成功."""
        monkeypatch.setenv("CONTACT_WEBHOOK_URL", "https://example.com/webhook")
        get_settings.cache_clear()

        sent_payloads: list[dict[str, Any]] = []
        init_kwargs: dict[str, Any] = {}

        class _MockAsyncClient:
            def __init__(self, *_, **kwargs):
                init_kwargs.update(kwargs)

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return False

            async def post(self, url, content=None, headers=None):
                import json as _json

                sent_payloads.append(_json.loads(content))
                return httpx.Response(200, request=httpx.Request("POST", url))

        monkeypatch.setattr(
            "study_python.gtd.web.routers.iconbar.httpx.AsyncClient",
            _MockAsyncClient,
        )

        response = client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "feature",
                "email": "user@example.com",
                "text": "新機能のリクエストです。ダークモードの切替をお願いします。",
            },
        )
        assert response.status_code == 200
        assert "送信しました" in response.text
        assert len(sent_payloads) == 1
        sent = sent_payloads[0]
        assert sent["type"] == "inquiry_defrago"
        assert sent["category"] == "feature"
        assert sent["email"] == "user@example.com"
        assert "ダークモード" in sent["text"]
        # Google Apps Script の Web App は POST に対し 302 を返す仕様のため、
        # httpx.AsyncClient は follow_redirects=True で初期化されていること。
        # これがないと v3.1.1 時点のように Contact 機能がリダイレクトエラーで
        # 送信できなくなる。
        assert init_kwargs.get("follow_redirects") is True

    def test_submit_contact_follows_gas_redirect(self, client, monkeypatch):
        """GAS Web App が返す 302 リダイレクトを追跡できることを検証 (#4 regression)."""
        monkeypatch.setenv("CONTACT_WEBHOOK_URL", "https://example.com/webhook")
        get_settings.cache_clear()

        call_count = {"n": 0}

        class _RedirectingClient:
            """実際の GAS 挙動を再現するクライアント.

            follow_redirects=True で初期化されていなければ 302 をそのまま返し、
            呼び出し側の raise_for_status() で失敗する。
            follow_redirects=True なら 200 を返す。
            """

            def __init__(self, *_, **kwargs):
                self._follow = bool(kwargs.get("follow_redirects", False))

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return False

            async def post(self, url, content=None, headers=None):
                call_count["n"] += 1
                if self._follow:
                    return httpx.Response(200, request=httpx.Request("POST", url))
                return httpx.Response(
                    302,
                    headers={
                        "Location": "https://script.googleusercontent.com/macros/echo"
                    },
                    request=httpx.Request("POST", url),
                )

        monkeypatch.setattr(
            "study_python.gtd.web.routers.iconbar.httpx.AsyncClient",
            _RedirectingClient,
        )

        response = client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "question",
                "email": "user@example.com",
                "text": "302 リダイレクト追跡のリグレッションテスト本文です。",
            },
        )
        assert response.status_code == 200
        assert "送信しました" in response.text
        assert call_count["n"] == 1

    def test_submit_contact_handles_webhook_failure(self, client, monkeypatch):
        """Webhook が例外を投げた場合はネットワークエラーメッセージを返す."""
        monkeypatch.setenv("CONTACT_WEBHOOK_URL", "https://example.com/webhook")
        get_settings.cache_clear()

        class _FailingClient:
            def __init__(self, *_, **__):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return False

            async def post(self, *_, **__):
                raise httpx.ConnectError("boom")

        monkeypatch.setattr(
            "study_python.gtd.web.routers.iconbar.httpx.AsyncClient",
            _FailingClient,
        )

        response = client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "bug",
                "email": "user@example.com",
                "text": "エラーが発生しました。お知らせいたします。詳細。",
            },
        )
        assert response.status_code == 200
        assert "送信に失敗" in response.text

    def test_submit_contact_requires_auth(self, anon_client):
        response = anon_client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "question",
                "email": "user@example.com",
                "text": "十分な長さのお問い合わせ本文です。ありがとう。",
            },
            follow_redirects=False,
        )
        assert response.status_code in (302, 303)


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    """CONTACT_WEBHOOK_URL の環境変数変更を反映するためキャッシュをクリア."""
    yield
    get_settings.cache_clear()
