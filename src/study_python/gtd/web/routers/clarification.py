"""明確化ルーター.

未分類アイテムを一覧表示し、個別または一括で4分類に振り分ける。
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


_VALID_TAGS = {"delegation", "project", "do_now", "task"}


def _get_context(request: Request, repo: DbGtdRepository) -> dict[str, object]:
    logic = ClarificationLogic(repo)
    items = logic.get_pending_items()
    return {
        "active_page": "/clarification",
        "items": items,
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
    """アイテムを4分類のいずれかに分類する（HTMX）."""
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
        "partials/clarification_list.html",
        _get_context(request, repo),
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
        "partials/clarification_list.html",
        _get_context(request, repo),
    )


@router.post("/bulk_classify", response_class=HTMLResponse)
async def bulk_classify(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """選択したアイテムを一括分類する（HTMX）.

    selected_ids が空の場合は全未分類アイテムを対象にする。
    """
    form = await request.form()
    bulk_tag = str(form.get("bulk_tag", "")).strip()
    selected_ids_raw = str(form.get("selected_ids", "")).strip()

    if bulk_tag in _VALID_TAGS:
        logic = ClarificationLogic(repo)
        items = logic.get_pending_items()

        if selected_ids_raw:
            selected_ids = {
                sid.strip() for sid in selected_ids_raw.split(",") if sid.strip()
            }
            items = [i for i in items if i.id in selected_ids]

        classifiers = {
            "delegation": logic.classify_as_delegation,
            "project": logic.classify_as_project,
            "do_now": logic.classify_as_do_now,
            "task": logic.classify_as_task,
        }
        classifier = classifiers[bulk_tag]
        for item in items:
            classifier(item.id)

        repo.flush_to_db()

    return templates.TemplateResponse(
        request,
        "partials/clarification_list.html",
        _get_context(request, repo),
    )


@router.post("/bulk_trash", response_class=HTMLResponse)
async def bulk_trash(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """選択したアイテムを一括でゴミ箱に移動する（HTMX）.

    selected_ids が空の場合は全未分類アイテムを対象にする。
    """
    form = await request.form()
    selected_ids_raw = str(form.get("selected_ids", "")).strip()

    logic = ClarificationLogic(repo)
    collection = CollectionLogic(repo)
    items = logic.get_pending_items()

    if selected_ids_raw:
        selected_ids = {
            sid.strip() for sid in selected_ids_raw.split(",") if sid.strip()
        }
        items = [i for i in items if i.id in selected_ids]

    for item in items:
        collection.move_to_trash(item.id)

    repo.flush_to_db()

    return templates.TemplateResponse(
        request,
        "partials/clarification_list.html",
        _get_context(request, repo),
    )
