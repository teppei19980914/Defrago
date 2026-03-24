"""設定ルーター."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from study_python.gtd.web.dependencies import require_auth


router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(require_auth)],
)
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request) -> HTMLResponse:
    """設定ページを表示する."""
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"active_page": "/settings"},
    )
