"""Web層テスト用フィクスチャ."""

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

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


def _make_app(test_session_factory, monkeypatch, password_hash):
    """テスト用アプリを構築する."""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-testing")
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", password_hash)
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
    password = "test-password"
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    app = _make_app(test_session_factory, monkeypatch, pw_hash)

    with TestClient(app, follow_redirects=False) as c:
        c.post("/login", data={"username": "admin", "password": password})
        yield c


@pytest.fixture
def anon_client(test_session_factory, monkeypatch):
    """未認証TestClient."""
    app = _make_app(test_session_factory, monkeypatch, "dummy")

    with TestClient(app, follow_redirects=False) as c:
        yield c
