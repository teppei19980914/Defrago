"""見直しルーター."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from study_python.gtd.logic.review import ReviewLogic
from study_python.gtd.models import Tag
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import (
    get_repository,
    require_auth,
    validate_item_id,
)
from study_python.gtd.web.template_engine import templates


router = APIRouter(
    prefix="/review",
    tags=["review"],
    dependencies=[Depends(require_auth)],
)


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


# --- プロジェクト計画ウィザード（ナチュラル・プランニング・モデル） ---


@router.get("/{item_id}/plan", response_class=HTMLResponse)
async def plan_wizard(
    item_id: str,
    request: Request,
    step: int = 1,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """プロジェクト計画ウィザードのステップを表示する（HTMX）."""
    validate_item_id(item_id)
    item = repo.get(item_id)
    if item is None or item.tag != Tag.PROJECT:
        return templates.TemplateResponse(
            request,
            "partials/item_list.html",
            {**_get_review_context(request, repo), "page": "review"},
        )
    return templates.TemplateResponse(
        request,
        "partials/plan_step.html",
        {"request": request, "item": item, "step": step, "brainstorm_items": []},
    )


@router.post("/{item_id}/plan/purpose", response_class=HTMLResponse)
async def save_purpose(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """Step 1-2: 目的と望ましい結果を保存する."""
    validate_item_id(item_id)
    form = await request.form()
    purpose = str(form.get("purpose", "")).strip()
    outcome = str(form.get("outcome", "")).strip()

    logic = ReviewLogic(repo)
    logic.save_project_plan(item_id, purpose=purpose, outcome=outcome)
    repo.flush_to_db()

    item = repo.get(item_id)
    return templates.TemplateResponse(
        request,
        "partials/plan_step.html",
        {"request": request, "item": item, "step": 3, "brainstorm_items": []},
    )


@router.post("/{item_id}/plan/brainstorm", response_class=HTMLResponse)
async def save_brainstorm(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """Step 3: ブレインストーミング結果を受け取り、Step 4へ進む."""
    validate_item_id(item_id)
    form = await request.form()
    raw = str(form.get("brainstorm_items", ""))
    brainstorm_items = [line.strip() for line in raw.split("\n") if line.strip()]

    item = repo.get(item_id)
    return templates.TemplateResponse(
        request,
        "partials/plan_step.html",
        {
            "request": request,
            "item": item,
            "step": 4,
            "brainstorm_items": brainstorm_items,
        },
    )


@router.post("/{item_id}/plan/execute", response_class=HTMLResponse)
async def execute_plan(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """組織化結果からサブタスクを生成し、実行フェーズに送る."""
    validate_item_id(item_id)
    form = await request.form()

    titles = form.getlist("task_title")
    deadlines = form.getlist("task_deadline")

    sub_tasks: list[dict[str, str | bool]] = []
    for i, title in enumerate(titles):
        title_str = str(title).strip()
        if not title_str:
            continue
        sub_tasks.append(
            {
                "title": title_str,
                "deadline": str(deadlines[i]) if i < len(deadlines) else "",
                "is_next_action": False,
            }
        )

    if sub_tasks:
        logic = ReviewLogic(repo)
        try:
            logic.decompose_project_planned(item_id, sub_tasks)
            repo.flush_to_db()
        except ValueError:
            pass

    return templates.TemplateResponse(
        request,
        "partials/item_list.html",
        {**_get_review_context(request, repo), "page": "review"},
    )
