"""ダッシュボードルーター."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.logic.execution import ExecutionLogic
from study_python.gtd.logic.organization import OrganizationLogic
from study_python.gtd.logic.review import ReviewLogic
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import get_repository, require_auth


router = APIRouter(tags=["dashboard"], dependencies=[Depends(require_auth)])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """ダッシュボードを表示する."""
    collection = CollectionLogic(repo)
    execution = ExecutionLogic(repo)
    organization = OrganizationLogic(repo)
    review = ReviewLogic(repo)

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
        },
    )
