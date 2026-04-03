"""FastAPI依存性注入."""

from __future__ import annotations

import re
from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from study_python.gtd.web.database import get_session_factory
from study_python.gtd.web.db_repository import DbGtdRepository


UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def validate_item_id(item_id: str) -> str:
    """item_idがUUID形式であることを検証する.

    Args:
        item_id: 検証するID文字列。

    Returns:
        検証済みのitem_id。

    Raises:
        HTTPException: UUID形式でない場合。
    """
    if not UUID_PATTERN.match(item_id):
        raise HTTPException(status_code=400, detail="Invalid item ID format")
    return item_id


def get_db_session() -> Generator[Session, None, None]:
    """DBセッションを生成する.

    Yields:
        SQLAlchemyセッション。
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def require_auth(request: Request) -> str:
    """認証を要求し、user_idを返す.

    Args:
        request: HTTPリクエスト。

    Returns:
        認証済みユーザーのuser_id。

    Raises:
        HTTPException: 未認証の場合。
    """
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return str(user_id)


def get_repository(
    request: Request,
    session: Session = Depends(get_db_session),
    user_id: str = Depends(require_auth),
) -> DbGtdRepository:
    """認証済みユーザーのリポジトリを取得する.

    user_idでフィルタされたリポジトリを返す。
    ロジック層・ルーター層がどう呼んでも、
    他ユーザーのデータにはアクセスできない。

    Args:
        request: HTTPリクエスト。
        session: DBセッション。
        user_id: 認証済みユーザーID。

    Returns:
        user_idフィルタ済みDbGtdRepositoryインスタンス。
    """
    return DbGtdRepository(session, user_id)
