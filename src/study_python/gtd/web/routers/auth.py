"""認証ルーター."""

from __future__ import annotations

import logging
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from study_python.gtd.web.auth import (
    register_user,
    validate_password,
    validate_username,
    verify_credentials,
)
from study_python.gtd.web.db_models import GtdItemRow, NotificationRow, UserRow
from study_python.gtd.web.dependencies import get_db_session, require_auth
from study_python.gtd.web.labels import load_labels
from study_python.gtd.web.template_engine import templates


logger = logging.getLogger(__name__)


router = APIRouter(tags=["auth"])

_login_attempts: dict[str, list[float]] = defaultdict(list)
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 300  # 5分


def _is_rate_limited(client_ip: str) -> bool:
    """ログイン試行回数が制限を超えているか判定する."""
    now = time.time()
    attempts = _login_attempts[client_ip]
    _login_attempts[client_ip] = [t for t in attempts if now - t < _WINDOW_SECONDS]
    return len(_login_attempts[client_ip]) >= _MAX_ATTEMPTS


def _record_attempt(client_ip: str) -> None:
    """ログイン試行を記録する."""
    _login_attempts[client_ip].append(time.time())


@router.get("/login", response_class=HTMLResponse, response_model=None)
async def login_page(request: Request) -> HTMLResponse | RedirectResponse:
    """ログインページを表示する."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request, "login.html", {})


@router.post("/login", response_model=None)
async def login(
    request: Request,
    db: Session = Depends(get_db_session),
) -> HTMLResponse | RedirectResponse:
    """ログインを処理する."""
    client_ip = request.client.host if request.client else "unknown"

    if _is_rate_limited(client_ip):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": load_labels()["auth"]["error_rate_limit"]},
            status_code=429,
        )

    form = await request.form()
    username = str(form.get("username", ""))
    password = str(form.get("password", ""))

    user = verify_credentials(db, username, password)
    if user is not None:
        _login_attempts.pop(client_ip, None)
        request.session.clear()
        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["last_active"] = time.time()
        return RedirectResponse(url="/", status_code=302)

    _record_attempt(client_ip)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": load_labels()["auth"]["error_credentials"]},
        status_code=401,
    )


@router.get("/register", response_class=HTMLResponse, response_model=None)
async def register_page(request: Request) -> HTMLResponse | RedirectResponse:
    """ユーザー登録ページを表示する."""
    if request.session.get("user_id"):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request, "register.html", {})


@router.post("/register", response_model=None)
async def register(
    request: Request,
    db: Session = Depends(get_db_session),
) -> HTMLResponse | RedirectResponse:
    """ユーザー登録を処理する."""
    if load_labels()["auth"].get("register_disabled"):
        return RedirectResponse(url="/register", status_code=302)

    client_ip = request.client.host if request.client else "unknown"

    if _is_rate_limited(client_ip):
        return templates.TemplateResponse(
            request,
            "register.html",
            {"error": load_labels()["auth"]["error_register_rate_limit"]},
            status_code=429,
        )

    form = await request.form()
    username = str(form.get("username", "")).strip()
    password = str(form.get("password", ""))
    password_confirm = str(form.get("password_confirm", ""))

    # バリデーション
    error = validate_username(username)
    if error:
        return templates.TemplateResponse(
            request, "register.html", {"error": error, "username": username}
        )

    error = validate_password(password)
    if error:
        return templates.TemplateResponse(
            request, "register.html", {"error": error, "username": username}
        )

    if password != password_confirm:
        return templates.TemplateResponse(
            request,
            "register.html",
            {
                "error": load_labels()["auth"]["error_password_mismatch"],
                "username": username,
            },
        )

    user = register_user(db, username, password)
    if user is None:
        _record_attempt(client_ip)
        return templates.TemplateResponse(
            request,
            "register.html",
            {
                "error": load_labels()["auth"]["error_username_taken"],
                "username": username,
            },
        )

    # 登録成功 → 自動ログイン
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["last_active"] = time.time()
    return RedirectResponse(url="/", status_code=302)


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """ログアウトを処理する."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@router.post("/settings/delete_account")
async def delete_account(
    request: Request,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db_session),
) -> RedirectResponse:
    """ログイン中ユーザーのアカウントと関連データを物理削除する (#6).

    削除対象:
      - GtdItemRow: 当該ユーザーの全GTDアイテム (Inbox/タスク/ゴミ箱を含む)
      - NotificationRow: 当該ユーザーの全通知
      - UserRow: ユーザー本体

    確認チェックボックス (confirm=yes) が送信されていない場合は削除せず
    設定画面にリダイレクトする。
    削除完了後はセッションをクリアしてログイン画面へ戻す。
    """
    form = await request.form()
    if str(form.get("confirm", "")).lower() != "yes":
        return RedirectResponse(url="/settings", status_code=303)

    items_deleted = db.query(GtdItemRow).filter(GtdItemRow.user_id == user_id).delete()
    notifs_deleted = (
        db.query(NotificationRow).filter(NotificationRow.user_id == user_id).delete()
    )
    user_deleted = db.query(UserRow).filter(UserRow.id == user_id).delete()
    db.flush()

    logger.warning(
        "Account deleted: user_id=%s items=%d notifications=%d user_rows=%d",
        user_id,
        items_deleted,
        notifs_deleted,
        user_deleted,
    )

    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
