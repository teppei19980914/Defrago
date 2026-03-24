"""認証ルーター."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from study_python.gtd.web.auth import verify_credentials


router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/login", response_class=HTMLResponse, response_model=None)
async def login_page(request: Request) -> HTMLResponse | RedirectResponse:
    """ログインページを表示する."""
    if request.session.get("username"):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request, "login.html", {})


@router.post("/login", response_model=None)
async def login(request: Request) -> HTMLResponse | RedirectResponse:
    """ログインを処理する."""
    form = await request.form()
    username = str(form.get("username", ""))
    password = str(form.get("password", ""))

    if verify_credentials(username, password):
        request.session["username"] = username
        return RedirectResponse(url="/", status_code=302)

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
