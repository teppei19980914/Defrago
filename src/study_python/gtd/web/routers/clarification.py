"""明確化ルーター.

エッセンシャル思考に基づき、Inboxの未分類アイテムを4つのタグに分類する。
質問形式（Yes/No）を廃止し、4つのボタンによる即時分類とスキップ・削除を提供する。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from study_python.gtd.logic.clarification import ClarificationLogic
from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import (
    get_repository,
    require_auth,
    validate_item_id,
)
from study_python.gtd.web.template_engine import templates


router = APIRouter(
    prefix="/clarification",
    tags=["clarification"],
    dependencies=[Depends(require_auth)],
)


def _get_context(request: Request, repo: DbGtdRepository) -> dict[str, object]:
    logic = ClarificationLogic(repo)
    items = logic.get_pending_items()
    current = items[0] if items else None
    return {
        "active_page": "/clarification",
        "items": items,
        "current": current,
        "total": len(items),
        "remaining": len(items),
        "index": 0 if not items else 1,
    }


@router.get("", response_class=HTMLResponse)
async def clarification_page(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """明確化ページを表示する."""
    return templates.TemplateResponse(
        request, "clarification.html", _get_context(request, repo)
    )


@router.post("/{item_id}/classify/{tag}", response_class=HTMLResponse)
async def classify(
    item_id: str,
    tag: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """アイテムを4分類のいずれかに分類する（HTMX）.

    tag: delegation, project, do_now, task のいずれか
    """
    validate_item_id(item_id)
    logic = ClarificationLogic(repo)

    classifiers = {
        "delegation": logic.classify_as_delegation,
        "project": logic.classify_as_project,
        "do_now": logic.classify_as_do_now,
        "task": logic.classify_as_task,
    }
    classifier = classifiers.get(tag)
    if classifier is not None:
        classifier(item_id)
        repo.flush_to_db()

    return templates.TemplateResponse(
        request,
        "partials/clarification_step.html",
        _get_context(request, repo),
    )


@router.post("/{item_id}/skip", response_class=HTMLResponse)
async def skip_item(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """アイテムをスキップして次のアイテムに進む（HTMX）.

    スキップしたアイテムはInboxに残ったまま次のアイテムを表示する。
    現在のアイテムを末尾に移動するため、updated_atを更新する。
    """
    validate_item_id(item_id)
    item = repo.get(item_id)
    if item is not None:
        item.touch()
        repo.flush_to_db()

    # スキップしたアイテムは末尾に回すため、明確化対象から除外する
    logic = ClarificationLogic(repo)
    items = [i for i in logic.get_pending_items() if i.id != item_id]
    current = items[0] if items else None
    context = {
        "active_page": "/clarification",
        "items": items,
        "current": current,
        "total": len(items),
        "remaining": len(items),
        "index": 0 if not items else 1,
    }
    return templates.TemplateResponse(
        request, "partials/clarification_step.html", context
    )


@router.post("/{item_id}/trash", response_class=HTMLResponse)
async def trash_item(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """アイテムをゴミ箱に移動する（HTMX）."""
    validate_item_id(item_id)
    collection = CollectionLogic(repo)
    collection.move_to_trash(item_id)
    repo.flush_to_db()

    return templates.TemplateResponse(
        request,
        "partials/clarification_step.html",
        _get_context(request, repo),
    )
