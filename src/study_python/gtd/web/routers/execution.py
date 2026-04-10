"""実行ルーター."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from study_python.gtd.logic.execution import ExecutionLogic
from study_python.gtd.models import get_status_enum_for_tag
from study_python.gtd.web.db_models import UserRow
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import (
    get_db_session,
    get_repository,
    require_auth,
    validate_item_id,
)
from study_python.gtd.web.labels import load_labels
from study_python.gtd.web.template_engine import templates


router = APIRouter(
    prefix="/execution",
    tags=["execution"],
    dependencies=[Depends(require_auth)],
)

_labels = load_labels()
TAG_DISPLAY = _labels["execution"]["tags"]
STATUS_DISPLAY = _labels["execution"]["statuses"]


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


VALID_TAG_FILTERS = {"all", "delegation", "do_now", "task"}


@router.get("", response_class=HTMLResponse)
async def execution_page(
    request: Request,
    tag: str = "all",
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """タスク一覧ページを表示する."""
    if tag not in VALID_TAG_FILTERS:
        tag = "all"
    return templates.TemplateResponse(
        request, "execution.html", _get_tasks_context(request, repo, tag)
    )


def _increment_completed_counter(db: Session, user_id: str, count: int = 1) -> None:
    """完了カウンタをインクリメントする."""
    if count <= 0:
        return
    user = db.query(UserRow).filter(UserRow.id == user_id).first()
    if user:
        user.completed_items_count = (user.completed_items_count or 0) + count
        db.flush()


@router.post("/{item_id}/status", response_class=HTMLResponse)
async def update_status(
    item_id: str,
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db_session),
) -> HTMLResponse:
    """ステータスを更新する（HTMX）."""
    validate_item_id(item_id)
    form = await request.form()
    new_status = str(form.get("status", ""))
    tag_filter = str(form.get("tag_filter", "all"))

    logic = ExecutionLogic(repo)
    try:
        result = logic.update_status(item_id, new_status)
        repo.flush_to_db()
        if result and result.is_done():
            _increment_completed_counter(db, user_id)
    except ValueError:
        pass

    return templates.TemplateResponse(
        request,
        "partials/task_list.html",
        _get_tasks_context(request, repo, tag_filter),
    )


@router.post("/bulk_status", response_class=HTMLResponse)
async def bulk_status_update(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db_session),
) -> HTMLResponse:
    """タスクのステータスを一括更新する（HTMX）.

    selected_ids が空の場合はフィルタ中の全タスクを対象にする。
    selected_ids にカンマ区切りの ID が指定された場合はそれだけを対象にする。
    タスクのタグが対応しないステータスの場合はスキップする。
    """
    form = await request.form()
    new_status = str(form.get("bulk_status", ""))
    tag_filter = str(form.get("tag_filter", "all"))
    selected_ids_raw = str(form.get("selected_ids", "")).strip()

    completed_count = 0
    if new_status:
        logic = ExecutionLogic(repo)

        if selected_ids_raw:
            selected_ids = {
                sid.strip() for sid in selected_ids_raw.split(",") if sid.strip()
            }
            tasks = [t for t in logic.get_active_tasks() if t.id in selected_ids]
        else:
            tasks = logic.get_active_tasks()
            if tag_filter != "all":
                tasks = [t for t in tasks if t.tag and t.tag.value == tag_filter]

        for task in tasks:
            try:
                result = logic.update_status(task.id, new_status)
                if result and result.is_done():
                    completed_count += 1
            except ValueError:
                continue
        repo.flush_to_db()
        _increment_completed_counter(db, user_id, completed_count)

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
    validate_item_id(item_id)
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
    validate_item_id(item_id)
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
