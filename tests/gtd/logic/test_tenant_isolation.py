"""テナント分離テスト.

異なるユーザーのデータが互いにアクセスできないことを検証する。
"""

from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from study_python.gtd.models import GtdItem, ItemStatus, Tag, TaskStatus
from study_python.gtd.web.database import Base
from study_python.gtd.web.db_repository import DbGtdRepository


def _setup_db():
    """テスト用DB・セッションを構築する."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return factory


class TestTenantIsolation:
    """テナント間のデータ分離テスト."""

    def test_different_users_see_only_own_items(self):
        """異なるユーザーは自分のアイテムのみ参照できる."""
        factory = _setup_db()

        # ユーザーAがアイテムを追加
        session_a = factory()
        repo_a = DbGtdRepository(session_a, "user-a")
        item_a = GtdItem(title="ユーザーAのタスク")
        repo_a.add(item_a)
        repo_a.flush_to_db()
        session_a.commit()
        session_a.close()

        # ユーザーBがアイテムを追加
        session_b = factory()
        repo_b = DbGtdRepository(session_b, "user-b")
        item_b = GtdItem(title="ユーザーBのタスク")
        repo_b.add(item_b)
        repo_b.flush_to_db()
        session_b.commit()
        session_b.close()

        # ユーザーAは自分のアイテムのみ見える
        session_a2 = factory()
        repo_a2 = DbGtdRepository(session_a2, "user-a")
        assert len(repo_a2.items) == 1
        assert repo_a2.items[0].title == "ユーザーAのタスク"
        session_a2.close()

        # ユーザーBは自分のアイテムのみ見える
        session_b2 = factory()
        repo_b2 = DbGtdRepository(session_b2, "user-b")
        assert len(repo_b2.items) == 1
        assert repo_b2.items[0].title == "ユーザーBのタスク"
        session_b2.close()

    def test_user_cannot_get_other_users_item_by_id(self):
        """他ユーザーのアイテムIDを指定しても取得できない."""
        factory = _setup_db()

        session_a = factory()
        repo_a = DbGtdRepository(session_a, "user-a")
        item_a = GtdItem(title="秘密のタスク")
        repo_a.add(item_a)
        repo_a.flush_to_db()
        session_a.commit()
        item_a_id = item_a.id
        session_a.close()

        # ユーザーBがユーザーAのitem_idで取得を試みる
        session_b = factory()
        repo_b = DbGtdRepository(session_b, "user-b")
        assert repo_b.get(item_a_id) is None
        session_b.close()

    def test_user_cannot_delete_other_users_item(self):
        """他ユーザーのアイテムを削除できない."""
        factory = _setup_db()

        session_a = factory()
        repo_a = DbGtdRepository(session_a, "user-a")
        item_a = GtdItem(title="守るべきタスク")
        repo_a.add(item_a)
        repo_a.flush_to_db()
        session_a.commit()
        item_a_id = item_a.id
        session_a.close()

        # ユーザーBが削除を試みる
        session_b = factory()
        repo_b = DbGtdRepository(session_b, "user-b")
        result = repo_b.remove(item_a_id)
        assert result is None  # 削除されない
        session_b.close()

        # ユーザーAのアイテムは無事
        session_a2 = factory()
        repo_a2 = DbGtdRepository(session_a2, "user-a")
        assert repo_a2.get(item_a_id) is not None
        session_a2.close()

    def test_flush_does_not_delete_other_users_items(self):
        """flush_to_dbで他ユーザーのアイテムが削除されない."""
        factory = _setup_db()

        # ユーザーAがアイテムを追加
        session_a = factory()
        repo_a = DbGtdRepository(session_a, "user-a")
        item_a = GtdItem(title="Aのタスク")
        repo_a.add(item_a)
        repo_a.flush_to_db()
        session_a.commit()
        session_a.close()

        # ユーザーBが空のリポジトリでflush（自分のアイテム0件を同期）
        session_b = factory()
        repo_b = DbGtdRepository(session_b, "user-b")
        repo_b.flush_to_db()
        session_b.commit()
        session_b.close()

        # ユーザーAのアイテムは残っている
        session_a2 = factory()
        repo_a2 = DbGtdRepository(session_a2, "user-a")
        assert len(repo_a2.items) == 1
        session_a2.close()

    def test_add_auto_assigns_user_id(self):
        """addしたアイテムにuser_idが自動付与される."""
        factory = _setup_db()

        session = factory()
        repo = DbGtdRepository(session, "my-user-id")
        item = GtdItem(title="新規タスク")
        repo.add(item)
        assert item.user_id == "my-user-id"
        session.close()

    def test_get_by_tag_filtered_by_user(self):
        """get_by_tagもユーザーフィルタが効いている."""
        factory = _setup_db()

        session = factory()
        repo_a = DbGtdRepository(session, "user-a")
        item = GtdItem(
            title="Aのタスク",
            tag=Tag.TASK,
            status=TaskStatus.NOT_STARTED.value,
            item_status=ItemStatus.INBOX,
        )
        repo_a.add(item)
        repo_a.flush_to_db()
        session.commit()
        session.close()

        session2 = factory()
        repo_b = DbGtdRepository(session2, "user-b")
        assert len(repo_b.get_by_tag(Tag.TASK)) == 0
        session2.close()

    def test_trash_isolation(self):
        """ゴミ箱内のアイテムも他ユーザーから見えない."""
        from study_python.gtd.logic.collection import CollectionLogic

        factory = _setup_db()

        session_a = factory()
        repo_a = DbGtdRepository(session_a, "user-a")
        col_a = CollectionLogic(repo_a)
        item_a = col_a.add_to_inbox("Aのタスク")
        col_a.move_to_trash(item_a.id)
        repo_a.flush_to_db()
        session_a.commit()
        session_a.close()

        session_b = factory()
        repo_b = DbGtdRepository(session_b, "user-b")
        assert len(repo_b.get_trash()) == 0
        assert repo_b.get(item_a.id) is None
        session_b.close()

    def test_restore_other_user_item_fails(self):
        """他ユーザーのゴミ箱アイテムを復元できない."""
        from study_python.gtd.logic.collection import CollectionLogic
        from study_python.gtd.logic.trash import TrashLogic

        factory = _setup_db()

        session_a = factory()
        repo_a = DbGtdRepository(session_a, "user-a")
        col_a = CollectionLogic(repo_a)
        item_a = col_a.add_to_inbox("Aのタスク")
        col_a.move_to_trash(item_a.id)
        repo_a.flush_to_db()
        session_a.commit()
        item_a_id = item_a.id
        session_a.close()

        session_b = factory()
        repo_b = DbGtdRepository(session_b, "user-b")
        trash_b = TrashLogic(repo_b)
        result = trash_b.restore(item_a_id)
        assert result is None
        session_b.close()

    def test_user_a_trash_count_does_not_include_user_b(self):
        """ユーザーごとのゴミ箱カウントが分離されている."""
        from study_python.gtd.logic.collection import CollectionLogic

        factory = _setup_db()

        session_a = factory()
        repo_a = DbGtdRepository(session_a, "user-a")
        col_a = CollectionLogic(repo_a)
        for i in range(3):
            item = col_a.add_to_inbox(f"Aのタスク{i}")
            col_a.move_to_trash(item.id)
        repo_a.flush_to_db()
        session_a.commit()
        session_a.close()

        session_b = factory()
        repo_b = DbGtdRepository(session_b, "user-b")
        col_b = CollectionLogic(repo_b)
        item_b = col_b.add_to_inbox("Bのタスク")
        col_b.move_to_trash(item_b.id)
        repo_b.flush_to_db()
        session_b.commit()

        # ユーザーBのゴミ箱には自分のアイテム1件のみ
        assert len(repo_b.get_trash()) == 1
        session_b.close()
