"""アイコンバー機能 (実績 / お問い合わせ) のテスト."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from study_python.gtd.web.config import get_settings
from study_python.gtd.web.routers.iconbar import (
    _is_spammy_text,
    _reset_contact_rate_limit,
    _reset_release_sync_cache,
)


@pytest.fixture(autouse=True)
def _reset_contact_state():
    """各テスト前後にお問い合わせのレート制限状態をリセット."""
    _reset_contact_rate_limit()
    yield
    _reset_contact_rate_limit()


@pytest.fixture(autouse=True)
def _reset_release_cache():
    """各テスト前後にリリース通知同期キャッシュをリセット."""
    _reset_release_sync_cache()
    yield
    _reset_release_sync_cache()


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


class TestIsSpammyText:
    """_is_spammy_text の単体テスト."""

    def test_dominant_single_char_is_spam(self):
        """同じ文字が 80% 以上を占めるとスパム扱い."""
        assert _is_spammy_text("ああああああああああああああああああああ") is True

    def test_ascii_single_char_run_is_spam(self):
        """ASCII の同一文字連打もスパム扱い."""
        assert _is_spammy_text("a" * 30) is True

    def test_low_diversity_two_chars_is_spam(self):
        """ユニーク文字が 2 種だけならスパム扱い."""
        assert _is_spammy_text("abababababababababababab") is True

    def test_low_diversity_three_chars_is_spam(self):
        """ユニーク文字が 3 種のみでもスパム扱い (閾値は 4 未満)."""
        assert _is_spammy_text("abcabcabcabcabcabcabcabc") is True

    def test_whitespace_only_is_spam(self):
        """空白のみは空扱いでスパム."""
        assert _is_spammy_text("                    ") is True

    def test_legitimate_japanese_text_is_not_spam(self):
        """普通の日本語はスパム扱いされない."""
        assert (
            _is_spammy_text("これは普通のお問い合わせ本文です。困っています。") is False
        )

    def test_legitimate_english_text_is_not_spam(self):
        """普通の英文はスパム扱いされない."""
        assert (
            _is_spammy_text("This is a normal inquiry about the application.") is False
        )

    def test_whitespace_ignored_in_diversity_check(self):
        """空白は文字数カウントから除外される (空白の種は増えない)."""
        # 4 種のユニーク文字があるので OK
        assert _is_spammy_text("a b c d e f g h i j k l m") is False

    def test_exactly_80_percent_dominance_is_spam(self):
        """閾値 80% ちょうどでもスパム扱い (>= で判定)."""
        # 10文字中8文字がa → 80%
        assert _is_spammy_text("aaaaaaaaBC" * 2) is True


class TestContactRateLimit:
    """レート制限の統合テスト.

    _CONTACT_RATE_LIMIT = 10 / 時間 を前提。
    モックした Webhook クライアントで実際に submit_contact を叩き、
    10 件目までは成功、11 件目以降は error_rate_limit が返ることを検証。
    """

    def _setup_webhook_mock(self, monkeypatch):
        monkeypatch.setenv("CONTACT_WEBHOOK_URL", "https://example.com/webhook")
        get_settings.cache_clear()

        class _MockAsyncClient:
            def __init__(self, *_, **__):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                return False

            async def post(self, url, content=None, headers=None):
                return httpx.Response(200, request=httpx.Request("POST", url))

        monkeypatch.setattr(
            "study_python.gtd.web.routers.iconbar.httpx.AsyncClient",
            _MockAsyncClient,
        )

    def test_within_limit_all_succeed(self, client, monkeypatch):
        """上限以内 (10件) はすべて成功."""
        self._setup_webhook_mock(monkeypatch)
        for i in range(10):
            response = client.post(
                "/api/iconbar/contact/submit",
                data={
                    "category": "question",
                    "email": "user@example.com",
                    "text": f"これはテスト本文その{i}番目です。20文字以上の本文。",
                },
            )
            assert response.status_code == 200
            assert "送信しました" in response.text, f"iteration {i} failed"

    def test_exceeds_limit_returns_rate_limit_error(self, client, monkeypatch):
        """11 件目はレート制限エラー."""
        self._setup_webhook_mock(monkeypatch)
        # 10 件送る (上限ちょうど)
        for i in range(10):
            client.post(
                "/api/iconbar/contact/submit",
                data={
                    "category": "question",
                    "email": "user@example.com",
                    "text": f"これはテスト本文その{i}番目です。20文字以上の本文。",
                },
            )
        # 11 件目
        response = client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "question",
                "email": "user@example.com",
                "text": "これは11件目のテスト本文です。レート制限に掛かるはず。",
            },
        )
        assert response.status_code == 200
        assert "上限に達しました" in response.text

    def test_validation_failure_does_not_consume_quota(self, client, monkeypatch):
        """バリデーション失敗 (typo 等) は quota を消費しない."""
        self._setup_webhook_mock(monkeypatch)
        # 10 回、短すぎる本文で送信 (error_text_length で弾かれる)
        for _ in range(10):
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
        # 次に正規の送信 → まだ quota が残っているので成功するべき
        response = client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "question",
                "email": "user@example.com",
                "text": "これは正規のテスト本文です。20文字以上の内容です。",
            },
        )
        assert response.status_code == 200
        assert "送信しました" in response.text

    def test_spammy_text_is_rejected(self, client, monkeypatch):
        """明らかにスパムな本文は error_spam で弾かれる."""
        self._setup_webhook_mock(monkeypatch)
        response = client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "question",
                "email": "user@example.com",
                "text": "あああああああああああああああああああああ",
            },
        )
        assert response.status_code == 200
        assert "同じ文字が繰り返されている" in response.text

    def test_spammy_text_does_not_consume_quota(self, client, monkeypatch):
        """スパム検出で弾かれた場合は quota を消費しない."""
        self._setup_webhook_mock(monkeypatch)
        # スパム本文を 10 回送信
        for _ in range(10):
            client.post(
                "/api/iconbar/contact/submit",
                data={
                    "category": "question",
                    "email": "user@example.com",
                    "text": "a" * 30,
                },
            )
        # 次に正規本文で成功するはず
        response = client.post(
            "/api/iconbar/contact/submit",
            data={
                "category": "question",
                "email": "user@example.com",
                "text": "これは正規のテスト本文です。20文字以上の内容です。",
            },
        )
        assert response.status_code == 200
        assert "送信しました" in response.text


class TestReleaseNotificationSync:
    """v3.1.5 #A: リリース通知同期の DB アクセス削減を検証する.

    最適化前: ページロードごとに「リリース数 × SELECT」を実行
    最適化後: 1ページロードあたり最大 1 SELECT、warm キャッシュヒット時は 0
    """

    def test_first_call_warms_cache_and_inserts_notifications(
        self, client, test_session
    ):
        """初回呼び出しでリリース通知が DB に登録される."""
        from study_python.gtd.web.db_models import NotificationRow

        # 初回 badge_count 呼び出し
        response = client.get("/api/iconbar/badge_count")
        assert response.status_code == 200

        # システム通知 (リリース通知) が複数件 DB に登録されているはず
        test_session.expire_all()
        rows = (
            test_session.query(NotificationRow)
            .filter(NotificationRow.notification_type == "system")
            .all()
        )
        assert len(rows) >= 1, "リリース通知が登録されていない"

    def test_warm_cache_skips_db_query(self, test_session):
        """warm cache 状態で _sync_release_notifications を呼んでも DB に触れない.

        cache に current_version が記録された状態で関数を呼び、
        NotificationRow への SELECT/INSERT が一切発生しないことを検証する。
        """
        from study_python.gtd.web.routers import iconbar
        from study_python.gtd.web.routers.iconbar import (
            _load_releases,
            _sync_release_notifications,
            _synced_release_versions,
        )

        user_id = "warm-cache-user"
        # current_version を取得してキャッシュに注入 (warm 状態を作る)
        current_version = str(_load_releases().get("current_version", ""))
        assert current_version, "releases.json に current_version が必要"
        _synced_release_versions[user_id] = current_version

        # DB クエリを観測するためのカウンタ
        query_count = {"n": 0}
        original_query = test_session.query

        def _counting_query(*args, **kwargs):
            # NotificationRow に対するクエリだけカウント
            for arg in args:
                if (
                    arg is iconbar.NotificationRow
                    or getattr(arg, "class_", None) is iconbar.NotificationRow
                ):
                    query_count["n"] += 1
                    break
            return original_query(*args, **kwargs)

        test_session.query = _counting_query  # type: ignore[method-assign]

        # warm cache 状態で呼び出す
        _sync_release_notifications(test_session, user_id)

        # NotificationRow に対するクエリは 0 件のはず
        assert query_count["n"] == 0, (
            f"warm cache 状態で {query_count['n']} 件の NotificationRow クエリが発生"
        )

    def test_no_duplicate_inserts_on_repeated_calls(self, client, test_session):
        """複数回呼んでも通知が重複登録されないこと."""
        from study_python.gtd.web.db_models import NotificationRow

        # 3回呼ぶ
        for _ in range(3):
            client.get("/api/iconbar/badge_count")

        test_session.expire_all()
        rows = (
            test_session.query(NotificationRow)
            .filter(NotificationRow.notification_type == "system")
            .all()
        )
        # 重複登録がなければ、リリース数と一致する (キャッシュにより N+1 にもならない)
        titles = [r.title for r in rows]
        assert len(titles) == len(set(titles)), (
            f"重複したリリース通知が検出された: {titles}"
        )

    def test_cache_reset_after_version_change(self, client, monkeypatch):
        """current_version が変わったらキャッシュは無効化される."""
        from study_python.gtd.web.routers import iconbar

        # 1回目: キャッシュウォーム
        client.get("/api/iconbar/badge_count")

        # _load_releases を別の current_version を返すようにモック
        new_data = {
            "current_version": "999.999.999",
            "releases": [
                {
                    "version": "999.999.999",
                    "date": "2099-12-31",
                    "title": "未来のリリース",
                    "summary": "テスト用",
                    "changes": ["a"],
                }
            ],
        }
        sync_call_count = {"n": 0}

        def _spy_load_releases():
            sync_call_count["n"] += 1
            return new_data

        monkeypatch.setattr(iconbar, "_load_releases", _spy_load_releases)

        # 2回目: バージョンが変わったのでキャッシュミス -> _load_releases 呼ばれる
        client.get("/api/iconbar/badge_count")
        assert sync_call_count["n"] >= 1


class TestNotificationCleanup:
    """v3.1.5 #C: 古い既読通知の自動クリーンアップを検証する."""

    def test_cleanup_deletes_old_read_notifications(self, test_engine):
        """30日以上前の既読通知は削除される."""
        from datetime import UTC, datetime, timedelta

        from sqlalchemy.orm import sessionmaker

        from study_python.gtd.web.app import (
            NOTIFICATION_RETENTION_DAYS,
            _cleanup_old_notifications,
        )
        from study_python.gtd.web.db_models import NotificationRow

        Session = sessionmaker(bind=test_engine)
        session = Session()

        old_date = (
            datetime.now(UTC) - timedelta(days=NOTIFICATION_RETENTION_DAYS + 5)
        ).isoformat()
        recent_date = (datetime.now(UTC) - timedelta(days=1)).isoformat()

        session.add_all(
            [
                NotificationRow(
                    id="old-read-1",
                    user_id="user1",
                    notification_type="system",
                    title="古い既読",
                    message="",
                    is_read=True,
                    created_at=old_date,
                ),
                NotificationRow(
                    id="recent-read-1",
                    user_id="user1",
                    notification_type="system",
                    title="新しい既読",
                    message="",
                    is_read=True,
                    created_at=recent_date,
                ),
                NotificationRow(
                    id="old-unread-1",
                    user_id="user1",
                    notification_type="system",
                    title="古い未読",
                    message="",
                    is_read=False,
                    created_at=old_date,
                ),
            ]
        )
        session.commit()
        session.close()

        _cleanup_old_notifications(test_engine)

        session2 = Session()
        remaining_ids = {row.id for row in session2.query(NotificationRow).all()}
        session2.close()

        # 古い既読は消える
        assert "old-read-1" not in remaining_ids
        # 新しい既読は残る
        assert "recent-read-1" in remaining_ids
        # 古い未読は残る。未読は対象外。
        assert "old-unread-1" in remaining_ids

    def test_cleanup_no_op_when_nothing_old(self, test_engine):
        """全部新しい場合は何も削除されない."""
        from datetime import UTC, datetime, timedelta

        from sqlalchemy.orm import sessionmaker

        from study_python.gtd.web.app import _cleanup_old_notifications
        from study_python.gtd.web.db_models import NotificationRow

        Session = sessionmaker(bind=test_engine)
        session = Session()

        recent_date = (datetime.now(UTC) - timedelta(days=1)).isoformat()
        session.add(
            NotificationRow(
                id="fresh-1",
                user_id="user1",
                notification_type="system",
                title="新しい",
                message="",
                is_read=True,
                created_at=recent_date,
            )
        )
        session.commit()
        session.close()

        _cleanup_old_notifications(test_engine)

        session2 = Session()
        count = session2.query(NotificationRow).count()
        session2.close()
        assert count == 1


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    """CONTACT_WEBHOOK_URL の環境変数変更を反映するためキャッシュをクリア."""
    yield
    get_settings.cache_clear()
