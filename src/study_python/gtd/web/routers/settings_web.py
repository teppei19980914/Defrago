"""設定ルーター."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from study_python.gtd.web.dependencies import require_auth
from study_python.gtd.web.template_engine import templates


router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(require_auth)],
)

STATIC_DIR = Path(__file__).parent.parent / "static"


def _get_current_version() -> str:
    """releases.jsonから最新バージョンを取得する."""
    path = STATIC_DIR / "releases.json"
    if not path.exists():
        return "0.0.0"
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("current_version", "0.0.0")


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request) -> HTMLResponse:
    """設定ページを表示する."""
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "active_page": "/settings",
            "app_version": _get_current_version(),
        },
    )
