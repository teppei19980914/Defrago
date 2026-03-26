"""認証ルーター."""

from __future__ import annotations

import time
from collections import defaultdict
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from study_python.gtd.web.auth import verify_credentials


router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

_login_attempts: dict[str, list[float]] = defaultdict(list)
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 300  # 5分


def _is_rate_limited(client_ip: str) -> bool:
    """ログイン試行回数が制限を超えているか判定する."""
    now = time.time()
    attempts = _login_attempts[client_ip]
    # ウィンドウ外の古い記録を除去
    _login_attempts[client_ip] = [t for t in attempts if now - t < _WINDOW_SECONDS]
    return len(_login_attempts[client_ip]) >= _MAX_ATTEMPTS


def _record_attempt(client_ip: str) -> None:
    """ログイン試行を記録する."""
    _login_attempts[client_ip].append(time.time())


@router.get("/login", response_class=HTMLResponse, response_model=None)
async def login_page(request: Request) -> HTMLResponse | RedirectResponse:
    """ログインページを表示する."""
    if request.session.get("username"):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request, "login.html", {})


@router.post("/login", response_model=None)
async def login(request: Request) -> HTMLResponse | RedirectResponse:
    """ログインを処理する."""
    client_ip = request.client.host if request.client else "unknown"

    if _is_rate_limited(client_ip):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": "ログイン試行回数が上限に達しました。しばらく待ってから再試行してください。"
            },
            status_code=429,
        )

    form = await request.form()
    username = str(form.get("username", ""))
    password = str(form.get("password", ""))

    if verify_credentials(username, password):
        # 成功時は記録をクリア
        _login_attempts.pop(client_ip, None)
        request.session["username"] = username
        return RedirectResponse(url="/", status_code=302)

    _record_attempt(client_ip)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": "ユーザー名またはパスワードが正しくありません"},
        status_code=401,
    )


@router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """ログアウトを処理する."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
