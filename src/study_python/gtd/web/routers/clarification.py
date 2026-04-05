"""明確化ルーター."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from study_python.gtd.logic.clarification import ClarificationLogic
from study_python.gtd.models import EnergyLevel, Location, TimeEstimate
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import get_repository, require_auth
from study_python.gtd.web.labels import load_labels
from study_python.gtd.web.template_engine import templates


router = APIRouter(
    prefix="/clarification",
    tags=["clarification"],
    dependencies=[Depends(require_auth)],
)

_cl = load_labels()["clarification"]
QUESTIONS = [_cl["question1"], _cl["question2"], _cl["question3"], _cl["question4"]]


def _get_context(
    request: Request,
    repo: DbGtdRepository,
    step: int = 0,
    show_context_form: bool = False,
) -> dict[str, object]:
    logic = ClarificationLogic(repo)
    items = logic.get_pending_items()
    current = items[0] if items else None
    return {
        "active_page": "/clarification",
        "items": items,
        "current": current,
        "step": step,
        "question": QUESTIONS[step] if step < len(QUESTIONS) else "",
        "total": len(items),
        "show_context_form": show_context_form,
        "locations": [
            (loc.value, name)
            for loc, name in zip(
                Location,
                [_cl["locations"][loc_.value] for loc_ in Location],
                strict=False,
            )
        ],
        "time_estimates": [
            (te.value, name)
            for te, name in zip(
                TimeEstimate,
                [_cl["time_estimates"][t.value] for t in TimeEstimate],
                strict=False,
            )
        ],
        "energy_levels": [
            (el.value, name)
            for el, name in zip(
                EnergyLevel,
                [_cl["energy_levels"][e.value] for e in EnergyLevel],
                strict=False,
            )
        ],
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


@router.post("/answer", response_class=HTMLResponse)
async def answer(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """ウィザードの回答を処理する（HTMX）."""
    form = await request.form()
    item_id = str(form.get("item_id", ""))
    step = int(form.get("step", "0"))
    choice = str(form.get("choice", ""))

    logic = ClarificationLogic(repo)

    if choice == "yes":
        if step == 0:
            return templates.TemplateResponse(
                request,
                "partials/clarification_step.html",
                _get_context(request, repo, step=1),
            )
        elif step == 1:
            logic.classify_as_calendar(item_id)
            repo.flush_to_db()
        elif step == 2:
            logic.classify_as_project(item_id)
            repo.flush_to_db()
        elif step == 3:
            logic.classify_as_do_now(item_id)
            repo.flush_to_db()
    elif choice == "no":
        if step == 0:
            logic.classify_as_delegation(item_id)
            repo.flush_to_db()
        elif step == 1:
            return templates.TemplateResponse(
                request,
                "partials/clarification_step.html",
                _get_context(request, repo, step=2),
            )
        elif step == 2:
            return templates.TemplateResponse(
                request,
                "partials/clarification_step.html",
                _get_context(request, repo, step=3),
            )
        elif step == 3:
            return templates.TemplateResponse(
                request,
                "partials/clarification_step.html",
                _get_context(request, repo, step=step, show_context_form=True),
            )

    return templates.TemplateResponse(
        request,
        "partials/clarification_step.html",
        _get_context(request, repo, step=0),
    )


@router.post("/classify_task", response_class=HTMLResponse)
async def classify_task(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
) -> HTMLResponse:
    """タスクとして分類する（Context付き、HTMX）."""
    form = await request.form()
    item_id = str(form.get("item_id", ""))
    location_values = form.getlist("locations")
    time_val = str(form.get("time_estimate", "30min"))
    energy_val = str(form.get("energy", "medium"))

    locations = (
        [Location(str(v)) for v in location_values]
        if location_values
        else [Location.DESK]
    )

    logic = ClarificationLogic(repo)
    logic.classify_as_task(
        item_id,
        locations=locations,
        time_estimate=TimeEstimate(time_val),
        energy=EnergyLevel(energy_val),
    )
    repo.flush_to_db()

    return templates.TemplateResponse(
        request,
        "partials/clarification_step.html",
        _get_context(request, repo, step=0),
    )
