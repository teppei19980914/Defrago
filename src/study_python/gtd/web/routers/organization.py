"""整理ルーター."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from study_python.gtd.logic.organization import OrganizationLogic
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import get_repository, require_auth


router = APIRouter(
    prefix="/organization",
    tags=["organization"],
    dependencies=[Depends(require_auth)],
)
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("", response_class=HTMLResponse)
async def organization_page(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """整理ページを表示する."""
    logic = OrganizationLogic(repo)
    items = logic.get_unorganized_tasks()
    current = items[0] if items else None
    quadrants = logic.get_matrix_quadrants()
    return templates.TemplateResponse(
        request,
        "organization.html",
        {
            "active_page": "/organization",
            "items": items,
            "current": current,
            "total": len(items),
            "quadrants": quadrants,
        },
    )


@router.post("/set_scores", response_class=HTMLResponse)
async def set_scores(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """重要度/緊急度を設定する（HTMX）."""
    form = await request.form()
    item_id = str(form.get("item_id", ""))
    importance = int(form.get("importance", "5"))
    urgency = int(form.get("urgency", "5"))

    logic = OrganizationLogic(repo)
    try:
        logic.set_importance_urgency(item_id, importance, urgency)
        repo.flush_to_db()
    except ValueError:
        pass

    items = logic.get_unorganized_tasks()
    current = items[0] if items else None
    quadrants = logic.get_matrix_quadrants()
    return templates.TemplateResponse(
        request,
        "partials/organization_form.html",
        {
            "items": items,
            "current": current,
            "total": len(items),
            "quadrants": quadrants,
        },
    )
