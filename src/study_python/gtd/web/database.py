"""データベース接続とセッション管理."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """SQLAlchemy宣言ベース."""


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(db_url: str | None = None) -> Engine:
    """SQLAlchemyエンジンを取得する.

    Args:
        db_url: データベースURL。Noneの場合は設定から取得。

    Returns:
        SQLAlchemyエンジン。
    """
    global _engine  # noqa: PLW0603
    if _engine is None or db_url is not None:
        if db_url is None:
            from study_python.gtd.web.config import get_settings

            db_url = get_settings().database_url
        _engine = create_engine(db_url, echo=False)
    return _engine


def get_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """セッションファクトリを取得する.

    Args:
        engine: SQLAlchemyエンジン。Noneの場合はデフォルトエンジンを使用。

    Returns:
        セッションファクトリ。
    """
    global _session_factory  # noqa: PLW0603
    if _session_factory is None or engine is not None:
        if engine is None:
            engine = get_engine()
        _session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _session_factory


def reset_globals() -> None:
    """テスト用にグローバル状態をリセットする."""
    global _engine, _session_factory  # noqa: PLW0603
    _engine = None
    _session_factory = None
