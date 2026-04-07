"""ゴミ箱ルーター."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from study_python.gtd.logic.trash import TrashLogic
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import (
    get_repository,
    require_auth,
    validate_item_id,
)
from study_python.gtd.web.template_engine import templates


router = APIRouter(
    prefix="/trash",
    tags=["trash"],
    dependencies=[Depends(require_auth)],
)


def _get_context(request: Request, repo: DbGtdRepository) -> dict[str, object]:
    logic = TrashLogic(repo)
    items = logic.get_trash_items()
    days_map = {item.id: logic.days_until_auto_delete(item) for item in items}
    return {
        "active_page": "/trash",
        "items": items,
        "days_map": days_map,
        "count": len(items),
    }


@router.get("", response_class=HTMLResponse)
async def trash_page(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """ゴミ箱ページを表示する."""
    return templates.TemplateResponse(
        request, "trash.html", _get_context(request, repo)
    )


@router.post("/{item_id}/restore", response_class=HTMLResponse)
async def restore_item(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """アイテムを復元する（HTMX）."""
    validate_item_id(item_id)
    logic = TrashLogic(repo)
    logic.restore(item_id)
    repo.flush_to_db()
    return templates.TemplateResponse(
        request, "partials/trash_list.html", _get_context(request, repo)
    )


@router.post("/{item_id}/delete", response_class=HTMLResponse)
async def delete_permanently(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """アイテムを物理削除する（HTMX）."""
    validate_item_id(item_id)
    logic = TrashLogic(repo)
    logic.delete_permanently(item_id)
    repo.flush_to_db()
    return templates.TemplateResponse(
        request, "partials/trash_list.html", _get_context(request, repo)
    )
