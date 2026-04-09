"""アイコンバー機能のルーター（通知・実績・お問い合わせ・リリース管理）."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from study_python.gtd.web.config import get_settings
from study_python.gtd.web.db_models import NotificationRow
from study_python.gtd.web.db_repository import DbGtdRepository
from study_python.gtd.web.dependencies import (
    get_db_session,
    get_repository,
    require_auth,
)
from study_python.gtd.web.labels import load_labels
from study_python.gtd.web.template_engine import templates


logger = logging.getLogger(__name__)


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
    """実績データを返す（HTMX）.

    表示項目（#1）:
      - Inbox追加数: ゴミ箱以外の全アイテム数
        (未分類・分類済み・完了済みをすべて含む)
      - 完了数: 完了済みアイテム数
      - 完了率: 完了数 / Inbox追加数 * 100 (%)
    """
    active_items = repo.get_active()
    inbox_added_count = len(active_items)
    done_count = sum(1 for i in active_items if i.is_done())
    completion_rate = (
        round(done_count / inbox_added_count * 100, 1) if inbox_added_count > 0 else 0.0
    )

    _al = load_labels()["modal_achievements"]
    badges: list[str] = []
    for threshold in MILESTONE_THRESHOLDS["total_tasks"]:
        if inbox_added_count >= threshold:
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
            "inbox_added_count": inbox_added_count,
            "done_count": done_count,
            "completion_rate": completion_rate,
            "badges": badges,
        },
    )


# --- お問い合わせ (#4) ---


_CONTACT_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_CONTACT_MIN_LEN = 20
_CONTACT_MAX_LEN = 2000
_CONTACT_VALID_CATEGORIES = {"question", "bug", "feature", "other"}


@router.get("/contact", response_class=HTMLResponse)
async def get_contact(request: Request) -> HTMLResponse:
    """お問い合わせフォームを返す（HTMX）."""
    return templates.TemplateResponse(
        request,
        "partials/modal_contact.html",
        {"submitted": False},
    )


def _render_contact_result(
    request: Request, *, success: bool, message_key: str
) -> HTMLResponse:
    """送信結果をレンダリングする."""
    labels = load_labels()["modal_contact"]
    return templates.TemplateResponse(
        request,
        "partials/modal_contact.html",
        {
            "submitted": True,
            "success": success,
            "message": labels.get(message_key, labels["error_validation"]),
        },
    )


@router.post("/contact/submit", response_class=HTMLResponse)
async def submit_contact(
    request: Request,
    user_id: str = Depends(require_auth),
) -> HTMLResponse:
    """お問い合わせを Google Apps Script (Google Sheets) へ送信する.

    環境変数 CONTACT_WEBHOOK_URL に GAS Web App の URL を設定する。
    未設定の場合はエラーメッセージを返す。
    """
    form = await request.form()
    category = str(form.get("category", "")).strip()
    email = str(form.get("email", "")).strip()
    text = str(form.get("text", "")).strip()

    # バリデーション
    if category not in _CONTACT_VALID_CATEGORIES:
        return _render_contact_result(
            request, success=False, message_key="error_validation"
        )
    if not _CONTACT_EMAIL_RE.match(email) or len(email) > 254:
        return _render_contact_result(request, success=False, message_key="error_email")
    if not (_CONTACT_MIN_LEN <= len(text) <= _CONTACT_MAX_LEN):
        return _render_contact_result(
            request, success=False, message_key="error_text_length"
        )

    settings = get_settings()
    webhook_url = settings.contact_webhook_url
    if not webhook_url:
        logger.warning("CONTACT_WEBHOOK_URL is not configured")
        return _render_contact_result(
            request, success=False, message_key="error_unavailable"
        )

    payload = {
        "type": "inquiry_defrago",
        "category": category,
        "email": email,
        "text": text,
        "user_key": user_id,
        "submitted_at": datetime.now(tz=UTC).isoformat(),
    }
    try:
        # Google Apps Script の Web App は仕様上、POST に対して 302 を返し
        # script.googleusercontent.com へリダイレクトさせるため、
        # follow_redirects=True を明示的に指定する必要がある
        # (httpx の既定は False で requests と異なる)。
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.post(
                webhook_url,
                content=json.dumps(payload),
                headers={"Content-Type": "text/plain"},
            )
            response.raise_for_status()
    except (httpx.HTTPError, ValueError) as exc:
        logger.error("Contact webhook request failed: %s", exc)
        return _render_contact_result(
            request, success=False, message_key="error_network"
        )

    logger.info("Contact submitted: user=%s category=%s", user_id, category)
    return _render_contact_result(request, success=True, message_key="success")


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
