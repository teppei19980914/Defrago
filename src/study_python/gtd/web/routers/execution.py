"""実行ルーター."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from study_python.gtd.logic.execution import ExecutionLogic
from study_python.gtd.models import get_status_enum_for_tag
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import get_repository, require_auth


router = APIRouter(
    prefix="/execution",
    tags=["execution"],
    dependencies=[Depends(require_auth)],
)
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

TAG_DISPLAY = {
    "delegation": "依頼",
    "calendar": "カレンダー",
    "do_now": "即実行",
    "task": "タスク",
}

STATUS_DISPLAY = {
    "not_started": "未着手",
    "waiting": "連絡待ち",
    "registered": "カレンダー登録済み",
    "in_progress": "実施中",
    "done": "完了",
}


def _sort_tasks_by_project(tasks: list) -> list:
    """プロジェクト派生タスクをグループ化・order順にソートする."""
    standalone = [t for t in tasks if t.parent_project_id is None]
    by_project: dict[str, list] = {}
    for task in tasks:
        if task.parent_project_id is not None:
            by_project.setdefault(task.parent_project_id, []).append(task)
    for group in by_project.values():
        group.sort(key=lambda t: t.order if t.order is not None else 0)

    result = list(standalone)
    for group in by_project.values():
        result.extend(group)
    return result


def _get_tasks_context(
    request: Request, repo: DbGtdRepository, tag_filter: str = "all"
) -> dict[str, object]:
    logic = ExecutionLogic(repo)
    tasks = logic.get_active_tasks()
    if tag_filter != "all":
        tasks = [t for t in tasks if t.tag and t.tag.value == tag_filter]

    tasks = _sort_tasks_by_project(tasks)

    # プロジェクトグループ情報を構築
    project_groups: dict[str, str] = {}
    for task in tasks:
        if task.parent_project_id and task.parent_project_id not in project_groups:
            project_groups[task.parent_project_id] = task.parent_project_title

    statuses_map: dict[str, list[tuple[str, str]]] = {}
    for t in tasks:
        if t.tag:
            enum = get_status_enum_for_tag(t.tag)
            if enum:
                statuses_map[t.id] = [
                    (s.value, STATUS_DISPLAY.get(s.value, s.value)) for s in enum
                ]

    return {
        "active_page": "/execution",
        "tasks": tasks,
        "tag_filter": tag_filter,
        "tag_display": TAG_DISPLAY,
        "status_display": STATUS_DISPLAY,
        "statuses_map": statuses_map,
        "project_groups": project_groups,
        "count": len(tasks),
    }


@router.get("", response_class=HTMLResponse)
async def execution_page(
    request: Request,
    tag: str = "all",
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """タスク一覧ページを表示する."""
    return templates.TemplateResponse(
        request, "execution.html", _get_tasks_context(request, repo, tag)
    )


@router.post("/{item_id}/status", response_class=HTMLResponse)
async def update_status(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """ステータスを更新する（HTMX）."""
    form = await request.form()
    new_status = str(form.get("status", ""))
    tag_filter = str(form.get("tag_filter", "all"))

    logic = ExecutionLogic(repo)
    try:
        logic.update_status(item_id, new_status)
        repo.flush_to_db()
    except ValueError:
        pass

    return templates.TemplateResponse(
        request,
        "partials/task_list.html",
        _get_tasks_context(request, repo, tag_filter),
    )


@router.post("/{item_id}/order_up", response_class=HTMLResponse)
async def order_up(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """順序を上に移動する（HTMX）."""
    form = await request.form()
    tag_filter = str(form.get("tag_filter", "all"))
    logic = ExecutionLogic(repo)
    logic.reorder_item(item_id, "up")
    repo.flush_to_db()
    return templates.TemplateResponse(
        request,
        "partials/task_list.html",
        _get_tasks_context(request, repo, tag_filter),
    )


@router.post("/{item_id}/order_down", response_class=HTMLResponse)
async def order_down(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """順序を下に移動する（HTMX）."""
    form = await request.form()
    tag_filter = str(form.get("tag_filter", "all"))
    logic = ExecutionLogic(repo)
    logic.reorder_item(item_id, "down")
    repo.flush_to_db()
    return templates.TemplateResponse(
        request,
        "partials/task_list.html",
        _get_tasks_context(request, repo, tag_filter),
    )
