"""ダッシュボードルーター."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from study_python.gtd.logic.clarification import ClarificationLogic
from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.logic.execution import ExecutionLogic
from study_python.gtd.logic.review import ReviewLogic
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import get_repository, require_auth
from study_python.gtd.web.labels import load_labels
from study_python.gtd.web.template_engine import templates


router = APIRouter(tags=["dashboard"], dependencies=[Depends(require_auth)])


def _get_next_action(
    collection: CollectionLogic,
    clarification: ClarificationLogic,
    execution: ExecutionLogic,
    review: ReviewLogic,
) -> dict[str, str]:
    """エッセンシャル思考に基づき、次にやるべきことを判定する.

    優先順位:
    1. Inboxに未分類アイテム → 明確化へ
    2. 見直し対象あり → 見直しへ
    3. 実行中タスクあり → 実行へ
    4. すべてクリア → Inboxへ

    Returns:
        message(表示テキスト), url(遷移先), label(ボタンラベル)を持つ辞書。
    """
    L = load_labels()["dashboard"]

    unclassified = clarification.get_pending_items()
    if unclassified:
        return {
            "message": f"{len(unclassified)}{L['guide_clarify']}",
            "url": "/clarification",
            "label": L["guide_clarify_btn"],
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

    return {
        "message": f"{len(active)}{L['guide_tasks']}",
        "url": "/execution",
        "label": L["guide_exec_btn"],
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """ダッシュボードを表示する."""
    collection = CollectionLogic(repo)
    clarification = ClarificationLogic(repo)
    execution = ExecutionLogic(repo)
    review = ReviewLogic(repo)

    next_action = _get_next_action(collection, clarification, execution, review)

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "active_page": "/",
            "inbox_count": len(collection.get_inbox_items()),
            "active_count": len(execution.get_active_tasks()),
            "completed_count": review.get_completed_count(),
            "total_count": len(repo.get_active()),
            "next_action": next_action,
        },
    )
