"""ロジックテスト共通フィクスチャ."""

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from study_python.gtd.web.database import Base
from study_python.gtd.web.db_repository import DbGtdRepository


@pytest.fixture
def test_engine():
    """テスト用インメモリDBエンジン."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """テスト用DBセッション."""
    factory = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    session = factory()
    yield session
    session.close()


@pytest.fixture
def repo(test_session) -> DbGtdRepository:
    """テスト用リポジトリ."""
    return DbGtdRepository(test_session)
