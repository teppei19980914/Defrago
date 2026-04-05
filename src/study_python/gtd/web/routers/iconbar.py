"""アイコンバー機能のルーター（通知・実績・お問い合わせ・リリース管理）."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from study_python.gtd.web.db_models import NotificationRow
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import (
    get_db_session,
    get_repository,
    require_auth,
)
from study_python.gtd.web.labels import load_labels
from study_python.gtd.web.template_engine import templates


router = APIRouter(
    prefix="/api/iconbar",
    tags=["iconbar"],
)

STATIC_DIR = Path(__file__).parent.parent / "static"


def _load_releases() -> dict:
    """releases.jsonを読み込む."""
    path = STATIC_DIR / "releases.json"
    if not path.exists():
        return {"current_version": "0.0.0", "releases": []}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


# --- リリース通知の自動配信 ---


def _sync_release_notifications(db: Session, user_id: str) -> None:
    """リリースノートに基づく開発者通知をユーザーに配信する.

    まだ配信されていないリリースの通知を自動生成する。
    dedup_key（notification_type + title）で重複を防止する。
    """
    data = _load_releases()
    for release in data.get("releases", []):
        title = f"v{release['version']} {release['title']}"
        existing = (
            db.query(NotificationRow)
            .filter(
                NotificationRow.user_id == user_id,
                NotificationRow.notification_type == "system",
                NotificationRow.title == title,
            )
            .first()
        )
        if existing is None:
            notif = NotificationRow(
                id=str(uuid.uuid4()),
                user_id=user_id,
                notification_type="system",
                title=title,
                message=release.get("summary", ""),
                is_read=False,
                created_at=release.get("date", datetime.now(tz=UTC).isoformat()),
            )
            db.add(notif)
    db.flush()


# --- 通知（受信ボックス） ---


@router.get("/notifications", response_class=HTMLResponse)
async def get_notifications(
    request: Request,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db_session),
) -> HTMLResponse:
    """通知一覧を返す（HTMX）."""
    _sync_release_notifications(db, user_id)
    rows = (
        db.query(NotificationRow)
        .filter(NotificationRow.user_id == user_id)
        .order_by(NotificationRow.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "partials/modal_inbox.html",
        {"notifications": rows},
    )


@router.get("/notifications/{notif_id}", response_class=HTMLResponse)
async def get_notification_detail(
    notif_id: str,
    request: Request,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db_session),
) -> HTMLResponse:
    """通知の詳細を返す（HTMX）."""
    row = (
        db.query(NotificationRow)
        .filter(
            NotificationRow.id == notif_id,
            NotificationRow.user_id == user_id,
        )
        .first()
    )
    if row is None:
        return HTMLResponse(
            f"<p class='muted-text'>{load_labels()['modal_inbox']['not_found']}</p>"
        )

    # 既読にする
    if not row.is_read:
        row.is_read = True
        db.flush()

    return templates.TemplateResponse(
        request,
        "partials/modal_inbox_detail.html",
        {"notification": row},
    )


@router.post("/notifications/read_all", response_class=HTMLResponse)
async def mark_all_read(
    request: Request,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db_session),
) -> HTMLResponse:
    """全通知を既読にする（HTMX）."""
    db.query(NotificationRow).filter(
        NotificationRow.user_id == user_id,
        NotificationRow.is_read == False,  # noqa: E712
    ).update({"is_read": True})
    db.flush()
    rows = (
        db.query(NotificationRow)
        .filter(NotificationRow.user_id == user_id)
        .order_by(NotificationRow.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "partials/modal_inbox.html",
        {"notifications": rows},
    )


# --- アップデート情報ページ ---


@router.get("/releases", response_class=HTMLResponse)
async def releases_page(request: Request) -> HTMLResponse:
    """アップデート情報ページ（別タブ表示）."""
    data = _load_releases()
    return templates.TemplateResponse(
        request,
        "releases.html",
        {
            "current_version": data.get("current_version", "0.0.0"),
            "releases": data.get("releases", []),
        },
    )


# --- 実績 ---

MILESTONE_THRESHOLDS = {
    "total_tasks": [5, 10, 25, 50, 100, 250, 500],
}


@router.get("/achievements", response_class=HTMLResponse)
async def get_achievements(
    request: Request,
    repo: DbGtdRepository = Depends(get_repository),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db_session),
) -> HTMLResponse:
    """実績データを返す（HTMX）."""
    tasks = repo.get_tasks()
    done_count = sum(1 for t in tasks if t.is_done())
    total_count = len(tasks) + done_count

    _al = load_labels()["modal_achievements"]
    badges: list[str] = []
    for threshold in MILESTONE_THRESHOLDS["total_tasks"]:
        if total_count >= threshold:
            badges.append(
                f"{_al['achievement_prefix']}{threshold}{_al['achievement_suffix']}"
            )

    for badge_label in badges:
        existing = (
            db.query(NotificationRow)
            .filter(
                NotificationRow.user_id == user_id,
                NotificationRow.notification_type == "achievement",
                NotificationRow.title == badge_label,
            )
            .first()
        )
        if existing is None:
            notif = NotificationRow(
                id=str(uuid.uuid4()),
                user_id=user_id,
                notification_type="achievement",
                title=badge_label,
                message=f"{badge_label}{_al['congrats_suffix']}",
                is_read=False,
                created_at=datetime.now(tz=UTC).isoformat(),
            )
            db.add(notif)
    db.flush()

    return templates.TemplateResponse(
        request,
        "partials/modal_achievements.html",
        {
            "total_count": total_count,
            "done_count": done_count,
            "active_count": len(tasks),
            "badges": badges,
        },
    )


# --- お問い合わせ ---


@router.get("/contact", response_class=HTMLResponse)
async def get_contact(request: Request) -> HTMLResponse:
    """お問い合わせモーダルを返す（HTMX）."""
    return templates.TemplateResponse(request, "partials/modal_contact.html", {})


# --- 通知バッジカウント ---


@router.get("/badge_count", response_class=HTMLResponse)
async def badge_count(
    request: Request,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db_session),
) -> HTMLResponse:
    """未読通知数を返す（HTMX）."""
    _sync_release_notifications(db, user_id)
    count = (
        db.query(NotificationRow)
        .filter(
            NotificationRow.user_id == user_id,
            NotificationRow.is_read == False,  # noqa: E712
        )
        .count()
    )
    badge_text = str(count) if count <= 9 else "9+"
    if count == 0:
        return HTMLResponse("")
    return HTMLResponse(f'<span class="icon-badge">{badge_text}</span>')
