"""Web層テスト用フィクスチャ."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from study_python.gtd.web.auth import register_user
from study_python.gtd.web.config import get_settings
from study_python.gtd.web.database import Base, reset_globals
from study_python.gtd.web.dependencies import get_db_session


@pytest.fixture(autouse=True)
def _reset_config_cache():
    """設定キャッシュをリセットする."""
    get_settings.cache_clear()
    reset_globals()
    yield
    get_settings.cache_clear()
    reset_globals()


@pytest.fixture
def test_engine():
    """テスト用インメモリDBエンジン（共有コネクション）."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session_factory(test_engine):
    """テスト用セッションファクトリ."""
    return sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture
def test_session(test_session_factory) -> Session:
    """テスト用DBセッション."""
    session = test_session_factory()
    yield session
    session.close()


def _make_app(test_session_factory, monkeypatch):
    """テスト用アプリを構築する."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("DEBUG", "true")

    get_settings.cache_clear()
    reset_globals()

    from study_python.gtd.web.app import create_app

    app = create_app()

    def override_session():
        session = test_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_session
    return app


@pytest.fixture
def client(test_session_factory, monkeypatch):
    """認証済みTestClient."""
    app = _make_app(test_session_factory, monkeypatch)

    # テスト用ユーザーをDBに登録
    session = test_session_factory()
    register_user(session, "testuser", "test-password")
    session.commit()
    session.close()

    with TestClient(app, follow_redirects=False) as c:
        c.post("/login", data={"username": "testuser", "password": "test-password"})
        yield c


@pytest.fixture
def anon_client(test_session_factory, monkeypatch):
    """未認証TestClient."""
    app = _make_app(test_session_factory, monkeypatch)

    with TestClient(app, follow_redirects=False) as c:
        yield c
