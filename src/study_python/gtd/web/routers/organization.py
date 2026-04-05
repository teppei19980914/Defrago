"""整理ルーター."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from study_python.gtd.logic.organization import OrganizationLogic
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import (
    get_repository,
    require_auth,
    validate_item_id,
)
from study_python.gtd.web.template_engine import templates


def _safe_int(value: object, default: int, min_val: int, max_val: int) -> int:
    """フォーム入力を安全に整数に変換する."""
    try:
        result = int(str(value))
        return max(min_val, min(result, max_val))
    except (ValueError, TypeError):
        return default


router = APIRouter(
    prefix="/organization",
    tags=["organization"],
    dependencies=[Depends(require_auth)],
)


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
    validate_item_id(item_id)
    importance = _safe_int(form.get("importance", "5"), 5, 1, 10)
    urgency = _safe_int(form.get("urgency", "5"), 5, 1, 10)

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
