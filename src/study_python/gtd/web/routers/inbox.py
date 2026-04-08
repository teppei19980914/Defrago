"""Inboxルーター.

エッセンシャル思考に基づき、入力時に直接分類できる4つのボタンを提供する。
分類されない場合はInboxに溜めて、後で「まとめて分類」できる。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.models import Tag
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import (
    get_repository,
    require_auth,
    validate_item_id,
)
from study_python.gtd.web.labels import load_labels
from study_python.gtd.web.template_engine import templates


router = APIRouter(
    prefix="/inbox", tags=["inbox"], dependencies=[Depends(require_auth)]
)

_VALID_TAGS = {tag.value for tag in Tag}


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
    # 分類済みアイテム（tagあり）は実行画面で扱うため、Inbox には
    # 未分類（tag=None）のアイテムのみを表示する。(#8)
    all_items = logic.get_unclassified_inbox_items()
    items = _sort_items_by_project(all_items)
    unclassified_count = len(all_items)

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
                (
                    f"/inbox/{item.id}/delete",
                    load_labels()["inbox"]["delete_button"],
                    True,
                ),
            ]
        else:
            actions_map[item.id] = [
                (
                    f"/inbox/{item.id}/delete",
                    load_labels()["inbox"]["delete_button"],
                    True,
                ),
            ]
    return {
        "items": items,
        "actions_map": actions_map,
        "project_groups": project_groups,
        "unclassified_count": unclassified_count,
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
    """アイテムを追加する（HTMX）.

    formのtagパラメータが指定されていれば直接分類する。
    指定されていなければ未分類でInboxに登録する。
    """
    form = await request.form()
    title = str(form.get("title", "")).strip()
    tag_value = str(form.get("tag", "")).strip()

    logic = CollectionLogic(repo)
    if title:
        try:
            tag = Tag(tag_value) if tag_value in _VALID_TAGS else None
            logic.add_to_inbox(title, tag=tag)
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
    """アイテムをゴミ箱に移動する（HTMX）."""
    validate_item_id(item_id)
    logic = CollectionLogic(repo)
    logic.move_to_trash(item_id)
    repo.flush_to_db()
    return templates.TemplateResponse(
        request, "partials/item_list.html", _get_inbox_context(request, repo)
    )


@router.post("/process_all")
async def process_all(
    repo: DbGtdRepository = Depends(get_repository),
) -> RedirectResponse:
    """明確化フェーズへリダイレクトする.

    Inbox内の未分類アイテムをそのまま明確化フェーズで処理する。
    中間状態（someday等）への移動は行わない。
    """
    return RedirectResponse(url="/clarification", status_code=303)


@router.post("/{item_id}/order_up", response_class=HTMLResponse)
async def order_up(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """順序を上に移動する（HTMX）."""
    validate_item_id(item_id)
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
    validate_item_id(item_id)
    logic = CollectionLogic(repo)
    logic.reorder_item(item_id, "down")
    repo.flush_to_db()
    return templates.TemplateResponse(
        request, "partials/item_list.html", _get_inbox_context(request, repo)
    )
