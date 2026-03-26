"""見直しルーター."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from study_python.gtd.logic.review import ReviewLogic
from study_python.gtd.models import Tag
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import (
    get_repository,
    require_auth,
    validate_item_id,
)


router = APIRouter(
    prefix="/review",
    tags=["review"],
    dependencies=[Depends(require_auth)],
)
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


def _get_review_context(request: Request, repo: DbGtdRepository) -> dict[str, object]:
    logic = ReviewLogic(repo)
    items = logic.get_review_items()
    return {
        "active_page": "/review",
        "items": items,
        "completed_count": logic.get_completed_count(),
        "project_count": logic.get_project_count(),
        "Tag": Tag,
    }


@router.get("", response_class=HTMLResponse)
async def review_page(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """見直しページを表示する."""
    return templates.TemplateResponse(
        request, "review.html", _get_review_context(request, repo)
    )


@router.post("/{item_id}/delete", response_class=HTMLResponse)
async def delete_item(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """アイテムを削除する（HTMX）."""
    validate_item_id(item_id)
    logic = ReviewLogic(repo)
    logic.delete_item(item_id)
    repo.flush_to_db()
    return templates.TemplateResponse(
        request,
        "partials/item_list.html",
        {**_get_review_context(request, repo), "page": "review"},
    )


@router.post("/{item_id}/to_inbox", response_class=HTMLResponse)
async def move_to_inbox(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """アイテムをInboxに戻す（HTMX）."""
    validate_item_id(item_id)
    logic = ReviewLogic(repo)
    logic.move_to_inbox(item_id)
    repo.flush_to_db()
    return templates.TemplateResponse(
        request,
        "partials/item_list.html",
        {**_get_review_context(request, repo), "page": "review"},
    )


@router.post("/{item_id}/decompose", response_class=HTMLResponse)
async def decompose_project(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """プロジェクトを分解する（HTMX）."""
    validate_item_id(item_id)
    form = await request.form()
    titles_raw = str(form.get("titles", ""))
    titles = [t.strip() for t in titles_raw.split("\n") if t.strip()]

    if titles:
        logic = ReviewLogic(repo)
        try:
            logic.decompose_project(item_id, titles)
            repo.flush_to_db()
        except ValueError:
            pass

    return templates.TemplateResponse(
        request,
        "partials/item_list.html",
        {**_get_review_context(request, repo), "page": "review"},
    )
