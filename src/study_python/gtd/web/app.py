"""FastAPI Webアプリケーション."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from study_python.gtd.web.config import get_settings
from study_python.gtd.web.database import Base, get_engine
from study_python.gtd.web.routers import (
    auth,
    clarification,
    dashboard,
    execution,
    iconbar,
    inbox,
    review,
    settings_web,
    trash,
)
from study_python.logging_config import setup_logging


logger = logging.getLogger(__name__)

TRASH_RETENTION_DAYS = 30
NOTIFICATION_RETENTION_DAYS = 30


def _migrate_schema(engine: object) -> None:
    """既存DBスキーマを最新化する.

    PostgreSQLとSQLite両対応の互換性ある構文を使用する。
    既存カラムの追加と、廃止カラムのデータマイグレーションを行う。
    """
    from sqlalchemy import inspect, text

    insp = inspect(engine)

    # users テーブルのマイグレーション
    if insp.has_table("users"):
        user_cols = {c["name"] for c in insp.get_columns("users")}
        user_new_columns = {
            "total_items_count": "INTEGER DEFAULT 0",
            "completed_items_count": "INTEGER DEFAULT 0",
        }
        with engine.begin() as conn:
            for col_name, col_def in user_new_columns.items():
                if col_name not in user_cols:
                    conn.execute(
                        text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                    )
                    logger.info(f"Migration: added column '{col_name}' to users")

    # gtd_items テーブルのマイグレーション
    if not insp.has_table("gtd_items"):
        return
    existing = {c["name"] for c in insp.get_columns("gtd_items")}
    new_columns = {
        "project_purpose": "TEXT DEFAULT ''",
        "project_outcome": "TEXT DEFAULT ''",
        "project_support_location": "TEXT DEFAULT ''",
        "is_next_action": "BOOLEAN DEFAULT FALSE",
        "deadline": "VARCHAR(50) DEFAULT ''",
        "user_id": "VARCHAR(36) NOT NULL DEFAULT ''",
        "deleted_at": "VARCHAR(50) DEFAULT ''",
    }
    with engine.begin() as conn:
        for col_name, col_def in new_columns.items():
            if col_name not in existing:
                conn.execute(
                    text(f"ALTER TABLE gtd_items ADD COLUMN {col_name} {col_def}")
                )
                logger.info(f"Migration: added column '{col_name}' to gtd_items")

        # 廃止されたCALENDARタグを持つアイテムをタスクに変換
        conn.execute(
            text(
                "UPDATE gtd_items SET tag = 'task', status = 'not_started' "
                "WHERE tag = 'calendar'"
            )
        )


def _cleanup_expired_trash(engine: object) -> None:
    """30日経過したゴミ箱アイテムを物理削除する.

    全ユーザーを横断するバッチ処理のため、user_idでフィルタしない。
    DbGtdRepositoryを経由せず、直接エンジン経由で実行する。
    """
    from sqlalchemy import text

    cutoff = (datetime.now(UTC) - timedelta(days=TRASH_RETENTION_DAYS)).isoformat()
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "DELETE FROM gtd_items "
                "WHERE item_status = 'trash' "
                "AND deleted_at != '' "
                "AND deleted_at < :cutoff"
            ),
            {"cutoff": cutoff},
        )
        if result.rowcount > 0:
            logger.info(f"Cleanup: deleted {result.rowcount} expired trash items")


def _cleanup_old_notifications(engine: object) -> None:
    """既読の通知で NOTIFICATION_RETENTION_DAYS 経過したものを物理削除する.

    notifications テーブルが永続蓄積するのを防ぎ、Free DB の storage 上限を
    保護するためのバッチ処理 (#C v3.1.5)。未読通知は対象外とし、ユーザーが
    気づくまで残す。

    全ユーザーを横断する SQL バッチで、DbGtdRepository を経由せず直接エンジン
    経由で実行する。
    """
    from sqlalchemy import text

    cutoff = (
        datetime.now(UTC) - timedelta(days=NOTIFICATION_RETENTION_DAYS)
    ).isoformat()
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "DELETE FROM notifications "
                "WHERE is_read = TRUE "
                "AND created_at != '' "
                "AND created_at < :cutoff"
            ),
            {"cutoff": cutoff},
        )
        if result.rowcount > 0:
            logger.info(f"Cleanup: deleted {result.rowcount} old read notifications")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """アプリケーションのライフサイクル管理."""
    setup_logging(level="INFO", log_to_file=True, log_to_console=True)
    engine = get_engine()
    Base.metadata.create_all(engine)
    _migrate_schema(engine)
    _cleanup_expired_trash(engine)
    _cleanup_old_notifications(engine)
    logger.info("Defrago Web started")
    yield


def create_app() -> FastAPI:
    """FastAPIアプリケーションを生成する.

    Returns:
        FastAPIアプリケーション。
    """
    settings = get_settings()

    app = FastAPI(title="Defrago GTD", lifespan=lifespan)

    # Session middleware with security flags
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        https_only=not settings.debug,
        same_site="lax",
        max_age=86400,
    )

    # Static files
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Security headers middleware
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        """HTTPセキュリティヘッダーを付与する."""
        if request.url.path.startswith("/static"):
            return await call_next(request)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'"
        )
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    # Auth redirect middleware
    @app.middleware("http")
    async def auth_redirect_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        """未認証のHTTPExceptionをリダイレクトに変換する."""
        from fastapi.exceptions import HTTPException

        try:
            response = await call_next(request)
        except HTTPException as e:
            if e.status_code == 303:
                return RedirectResponse(url="/login", status_code=302)
            raise
        return response

    # Routers
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(inbox.router)
    app.include_router(clarification.router)
    app.include_router(execution.router)
    app.include_router(review.router)
    app.include_router(trash.router)
    app.include_router(settings_web.router)
    app.include_router(iconbar.router)

    return app


app = create_app()
