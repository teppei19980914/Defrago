"""ダッシュボードルーター."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from study_python.gtd.logic.clarification import ClarificationLogic
from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.logic.execution import ExecutionLogic
from study_python.gtd.logic.organization import OrganizationLogic
from study_python.gtd.logic.review import ReviewLogic
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import get_repository, require_auth


router = APIRouter(tags=["dashboard"], dependencies=[Depends(require_auth)])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


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
    # 1. Inboxに未処理アイテムがある → 収集フェーズへ
    inbox_items = collection.get_inbox_items()
    if inbox_items:
        return {
            "message": f"{len(inbox_items)}件のアイテムが頭の中にあります",
            "url": "/inbox",
            "label": "書き出す",
        }

    # 2. 明確化待ちアイテムがある → 明確化フェーズへ
    pending = clarification.get_pending_items()
    if pending:
        return {
            "message": f"{len(pending)}件のアイテムを分類しましょう",
            "url": "/clarification",
            "label": "明確化する",
        }

    # 3. 整理待ちアイテムがある → 整理フェーズへ
    unorganized = organization.get_unorganized_tasks()
    if unorganized:
        return {
            "message": f"{len(unorganized)}件のタスクに優先度を設定しましょう",
            "url": "/organization",
            "label": "整理する",
        }

    # 4. 見直し対象がある → 見直しフェーズへ
    review_items = review.get_review_items()
    if review_items:
        return {
            "message": f"{len(review_items)}件の見直し対象があります",
            "url": "/review",
            "label": "見直す",
        }

    # 5. 実行中タスクがある or すべて完了
    active = execution.get_active_tasks()
    if not active:
        return {
            "message": "頭の中はクリアです。フロー状態を楽しみましょう！",
            "url": "/inbox",
            "label": "新しく書き出す",
        }

    # Q1（重要かつ緊急）のタスクを優先表示
    q1_tasks = [
        t
        for t in active
        if t.importance is not None
        and t.urgency is not None
        and t.importance > 5
        and t.urgency > 5
    ]
    top_message = (
        f"最優先: {q1_tasks[0].title}"
        if q1_tasks
        else f"{len(active)}件のタスクがあります"
    )
    return {"message": top_message, "url": "/execution", "label": "実行する"}


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
