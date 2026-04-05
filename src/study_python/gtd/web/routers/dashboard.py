"""ダッシュボードルーター."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from study_python.gtd.logic.clarification import ClarificationLogic
from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.logic.execution import ExecutionLogic
from study_python.gtd.logic.organization import OrganizationLogic
from study_python.gtd.logic.review import ReviewLogic
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import get_repository, require_auth
from study_python.gtd.web.labels import load_labels
from study_python.gtd.web.template_engine import templates


router = APIRouter(tags=["dashboard"], dependencies=[Depends(require_auth)])


def _get_next_action(
    collection: CollectionLogic,
    clarification: ClarificationLogic,
    organization: OrganizationLogic,
    execution: ExecutionLogic,
    review: ReviewLogic,
) -> dict[str, str]:
    """GTDフローに基づき、次にやるべきことを判定する.

    Returns:
        message(表示テキスト), url(遷移先), label(ボタンラベル)を持つ辞書。
    """
    L = load_labels()["dashboard"]

    inbox_items = collection.get_inbox_items()
    if inbox_items:
        return {
            "message": f"{len(inbox_items)}{L['guide_inbox']}",
            "url": "/inbox",
            "label": L["guide_inbox_btn"],
        }

    pending = clarification.get_pending_items()
    if pending:
        return {
            "message": f"{len(pending)}{L['guide_clarify']}",
            "url": "/clarification",
            "label": L["guide_clarify_btn"],
        }

    unorganized = organization.get_unorganized_tasks()
    if unorganized:
        return {
            "message": f"{len(unorganized)}{L['guide_organize']}",
            "url": "/organization",
            "label": L["guide_organize_btn"],
        }

    review_items = review.get_review_items()
    if review_items:
        return {
            "message": f"{len(review_items)}{L['guide_review']}",
            "url": "/review",
            "label": L["guide_review_btn"],
        }

    active = execution.get_active_tasks()
    if not active:
        return {
            "message": L["guide_clear"],
            "url": "/inbox",
            "label": L["guide_clear_btn"],
        }

    q1_tasks = [
        t
        for t in active
        if t.importance is not None
        and t.urgency is not None
        and t.importance > 5
        and t.urgency > 5
    ]
    top_message = (
        f"{L['guide_priority']}{q1_tasks[0].title}"
        if q1_tasks
        else f"{len(active)}{L['guide_tasks']}"
    )
    return {"message": top_message, "url": "/execution", "label": L["guide_exec_btn"]}


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """ダッシュボードを表示する."""
    collection = CollectionLogic(repo)
    clarification = ClarificationLogic(repo)
    execution = ExecutionLogic(repo)
    organization = OrganizationLogic(repo)
    review = ReviewLogic(repo)

    next_action = _get_next_action(
        collection, clarification, organization, execution, review
    )
    quadrants = organization.get_matrix_quadrants()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "active_page": "/",
            "inbox_count": len(collection.get_inbox_items()),
            "active_count": len(execution.get_active_tasks()),
            "completed_count": review.get_completed_count(),
            "total_count": len(repo.items),
            "quadrants": quadrants,
            "next_action": next_action,
        },
    )
