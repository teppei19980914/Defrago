"""FastAPI依存性注入."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from study_python.gtd.web.database import get_session_factory
from study_python.gtd.web.db_repository import DbGtdRepository


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


def get_repository(
    session: Session = Depends(get_db_session),
) -> DbGtdRepository:
    """リポジトリを取得する.

    Args:
        session: DBセッション。

    Returns:
        DbGtdRepositoryインスタンス。
    """
    return DbGtdRepository(session)


def require_auth(request: Request) -> str:
    """認証を要求する.

    Args:
        request: HTTPリクエスト。

    Returns:
        認証済みユーザー名。

    Raises:
        HTTPException: 未認証の場合。
    """
    username = request.session.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return str(username)
