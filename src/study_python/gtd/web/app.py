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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """アプリケーションのライフサイクル管理."""
    setup_logging(level="INFO", log_to_file=True, log_to_console=True)
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("MindFlow Web started")
    yield


def create_app() -> FastAPI:
    """FastAPIアプリケーションを生成する.

    Returns:
        FastAPIアプリケーション。
    """
    settings = get_settings()

    app = FastAPI(title="MindFlow GTD", lifespan=lifespan)

    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

    # Static files
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

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
