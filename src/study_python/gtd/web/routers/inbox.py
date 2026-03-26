"""Inboxルーター."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import get_repository, require_auth


router = APIRouter(
    prefix="/inbox", tags=["inbox"], dependencies=[Depends(require_auth)]
)
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


def _sort_items_by_project(items: list) -> list:
    """プロジェクト派生アイテムをグループ化・order順にソートする."""
    standalone = [i for i in items if i.parent_project_id is None]
    by_project: dict[str, list] = {}
    for item in items:
        if item.parent_project_id is not None:
            by_project.setdefault(item.parent_project_id, []).append(item)
    for group in by_project.values():
        group.sort(key=lambda i: i.order if i.order is not None else 0)

    result = list(standalone)
    for group in by_project.values():
        result.extend(group)
    return result


def _get_inbox_context(request: Request, repo: DbGtdRepository) -> dict[str, object]:
    logic = CollectionLogic(repo)
    items = _sort_items_by_project(logic.get_inbox_items())

    # プロジェクトグループ情報を構築
    project_groups: dict[str, str] = {}
    for item in items:
        if item.parent_project_id and item.parent_project_id not in project_groups:
            project_groups[item.parent_project_id] = item.parent_project_title

    actions_map = {}
    for item in items:
        if item.parent_project_id is not None:
            actions_map[item.id] = [
                (f"/inbox/{item.id}/order_up", "▲", False),
                (f"/inbox/{item.id}/order_down", "▼", False),
                (f"/inbox/{item.id}/someday", "いつかやる", False),
                (f"/inbox/{item.id}/reference", "参考資料", False),
                (f"/inbox/{item.id}/delete", "削除", True),
            ]
        else:
            actions_map[item.id] = [
                (f"/inbox/{item.id}/someday", "いつかやる", False),
                (f"/inbox/{item.id}/reference", "参考資料", False),
                (f"/inbox/{item.id}/delete", "削除", True),
            ]
    return {
        "items": items,
        "actions_map": actions_map,
        "project_groups": project_groups,
        "active_page": "/inbox",
    }


@router.get("", response_class=HTMLResponse)
async def inbox_page(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """Inboxページを表示する."""
    return templates.TemplateResponse(
        request, "inbox.html", _get_inbox_context(request, repo)
    )


@router.post("/add", response_class=HTMLResponse)
async def add_item(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """アイテムを追加する（HTMX）."""
    form = await request.form()
    title = str(form.get("title", "")).strip()
    logic = CollectionLogic(repo)
    if title:
        try:
            logic.add_to_inbox(title)
            repo.flush_to_db()
        except ValueError:
            pass
    return templates.TemplateResponse(
        request, "partials/item_list.html", _get_inbox_context(request, repo)
    )


@router.post("/{item_id}/delete", response_class=HTMLResponse)
async def delete_item(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """アイテムを削除する（HTMX）."""
    logic = CollectionLogic(repo)
    logic.delete_item(item_id)
    repo.flush_to_db()
    return templates.TemplateResponse(
        request, "partials/item_list.html", _get_inbox_context(request, repo)
    )


@router.post("/{item_id}/someday", response_class=HTMLResponse)
async def move_to_someday(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """アイテムを「いつかやる」に移動する（HTMX）."""
    logic = CollectionLogic(repo)
    logic.move_to_someday(item_id)
    repo.flush_to_db()
    return templates.TemplateResponse(
        request, "partials/item_list.html", _get_inbox_context(request, repo)
    )


@router.post("/{item_id}/reference", response_class=HTMLResponse)
async def move_to_reference(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """アイテムを参考資料に移動する（HTMX）."""
    logic = CollectionLogic(repo)
    logic.move_to_reference(item_id)
    repo.flush_to_db()
    return templates.TemplateResponse(
        request, "partials/item_list.html", _get_inbox_context(request, repo)
    )


@router.post("/{item_id}/order_up", response_class=HTMLResponse)
async def order_up(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """順序を上に移動する（HTMX）."""
    logic = CollectionLogic(repo)
    logic.reorder_item(item_id, "up")
    repo.flush_to_db()
    return templates.TemplateResponse(
        request, "partials/item_list.html", _get_inbox_context(request, repo)
    )


@router.post("/{item_id}/order_down", response_class=HTMLResponse)
async def order_down(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """順序を下に移動する（HTMX）."""
    logic = CollectionLogic(repo)
    logic.reorder_item(item_id, "down")
    repo.flush_to_db()
    return templates.TemplateResponse(
        request, "partials/item_list.html", _get_inbox_context(request, repo)
    )
