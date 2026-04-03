"""FastAPI Webアプリケーション."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
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
    inbox,
    organization,
    review,
    settings_web,
)
from study_python.logging_config import setup_logging


logger = logging.getLogger(__name__)


def _migrate_add_project_planning_columns(engine: object) -> None:
    """プロジェクト計画カラムを既存テーブルに追加するマイグレーション."""
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    if not insp.has_table("gtd_items"):
        return
    existing = {c["name"] for c in insp.get_columns("gtd_items")}
    new_columns = {
        "project_purpose": "TEXT DEFAULT ''",
        "project_outcome": "TEXT DEFAULT ''",
        "project_support_location": "TEXT DEFAULT ''",
        "is_next_action": "BOOLEAN DEFAULT 0",
        "deadline": "VARCHAR(50) DEFAULT ''",
    }
    with engine.begin() as conn:
        for col_name, col_def in new_columns.items():
            if col_name not in existing:
                conn.execute(
                    text(f"ALTER TABLE gtd_items ADD COLUMN {col_name} {col_def}")
                )
                logger.info(f"Migration: added column '{col_name}' to gtd_items")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """アプリケーションのライフサイクル管理."""
    setup_logging(level="INFO", log_to_file=True, log_to_console=True)
    engine = get_engine()
    Base.metadata.create_all(engine)
    _migrate_add_project_planning_columns(engine)
    logger.info("MindFlow Web started")
    yield


def create_app() -> FastAPI:
    """FastAPIアプリケーションを生成する.

    Returns:
        FastAPIアプリケーション。
    """
    settings = get_settings()

    app = FastAPI(title="MindFlow GTD", lifespan=lifespan)

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
    app.include_router(organization.router)
    app.include_router(execution.router)
    app.include_router(review.router)
    app.include_router(settings_web.router)

    return app


app = create_app()
