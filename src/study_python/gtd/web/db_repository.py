"""SQLAlchemy永続化リポジトリ.

リクエストスコープでインメモリにアイテムを保持し、
flush_to_dbでDB同期する。ロジック層はGtdRepositoryProtocolを通じて利用する。

すべてのデータアクセスはuser_idでフィルタされる。
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from study_python.gtd.models import (
    EnergyLevel,
    GtdItem,
    ItemStatus,
    Location,
    Tag,
    TimeEstimate,
)
from study_python.gtd.web.db_models import GtdItemRow


logger = logging.getLogger(__name__)


class DbGtdRepository:
    """SQLAlchemy永続化リポジトリ（user_idスコープ）.

    リクエストごとに指定user_idのアイテムのみをメモリに読み込み、
    ロジック層のin-place変更後にflush_to_dbでDB同期する。

    Args:
        session: SQLAlchemyセッション。
        user_id: フィルタ対象のユーザーID。
    """

    def __init__(self, session: Session, user_id: str = "") -> None:
        self._session = session
        self._user_id = user_id
        self._items: list[GtdItem] = []
        self._index: dict[str, GtdItem] = {}
        self._load_all()

    @property
    def user_id(self) -> str:
        """現在のユーザーIDを返す."""
        return self._user_id

    def _load_all(self) -> None:
        """指定user_idのアイテムのみをDBから読み込む."""
        query = self._session.query(GtdItemRow)
        if self._user_id:
            query = query.filter(GtdItemRow.user_id == self._user_id)
        rows = query.all()
        self._items = [self._row_to_item(r) for r in rows]
        self._index = {item.id: item for item in self._items}

    @property
    def items(self) -> list[GtdItem]:
        """全アイテムのリストを返す."""
        return self._items

    def add(self, item: GtdItem) -> None:
        """アイテムを追加する（user_idを自動付与）.

        Args:
            item: 追加するアイテム。
        """
        item.user_id = self._user_id
        self._items.append(item)
        self._index[item.id] = item

    def remove(self, item_id: str) -> GtdItem | None:
        """アイテムをIDで物理削除する.

        Args:
            item_id: 削除するアイテムのID。

        Returns:
            削除したアイテム。見つからない場合はNone。
        """
        item = self._index.pop(item_id, None)
        if item is not None:
            self._items.remove(item)
        return item

    def get(self, item_id: str) -> GtdItem | None:
        """IDでアイテムを取得する（O(1)）.

        user_idスコープ内のアイテムのみ返す。

        Args:
            item_id: 取得するアイテムのID。

        Returns:
            アイテム。見つからない場合はNone。
        """
        return self._index.get(item_id)

    def get_by_status(self, status: ItemStatus) -> list[GtdItem]:
        """ItemStatusでフィルタリングしたアイテムを返す.

        Args:
            status: フィルタ条件のItemStatus。

        Returns:
            該当するアイテムのリスト。
        """
        return [i for i in self._items if i.item_status == status]

    def get_by_tag(self, tag: Tag) -> list[GtdItem]:
        """タグでフィルタリングしたアイテムを返す.

        Args:
            tag: フィルタ条件のTag。

        Returns:
            該当するアイテムのリスト。
        """
        return [i for i in self._items if i.tag == tag]

    def get_tasks(self) -> list[GtdItem]:
        """タスク化済みアイテムを返す.

        Returns:
            タスク化済みアイテムのリスト。
        """
        return [i for i in self._items if i.is_task()]

    def flush_to_db(self) -> None:
        """インメモリ状態をDBに同期する（user_idスコープ内のみ）.

        mergeで既存行を更新し、削除されたアイテムはDBからも削除する。
        """
        current_ids = {item.id for item in self._items}

        # DB上にあってメモリにないアイテムを削除（自分のデータのみ）
        query = self._session.query(GtdItemRow)
        if self._user_id:
            query = query.filter(GtdItemRow.user_id == self._user_id)
        db_rows = query.all()
        for row in db_rows:
            if row.id not in current_ids:
                self._session.delete(row)

        # メモリのアイテムをmerge（insert or update）
        for item in self._items:
            item.user_id = self._user_id
            self._session.merge(self._item_to_row(item))
        self._session.flush()
        logger.debug(f"Flushed {len(self._items)} items to DB for user={self._user_id}")

    @staticmethod
    def _row_to_item(row: GtdItemRow) -> GtdItem:
        """DBの行からGtdItemを復元する."""
        locations = (
            [Location(v) for v in json.loads(row.locations_json)]
            if row.locations_json
            else []
        )
        return GtdItem(
            id=row.id,
            user_id=row.user_id,
            title=row.title,
            created_at=row.created_at,
            updated_at=row.updated_at,
            note=row.note or "",
            item_status=ItemStatus(row.item_status),
            tag=Tag(row.tag) if row.tag else None,
            status=row.status,
            locations=locations,
            time_estimate=TimeEstimate(row.time_estimate)
            if row.time_estimate
            else None,
            energy=EnergyLevel(row.energy) if row.energy else None,
            importance=row.importance,
            urgency=row.urgency,
            project_purpose=row.project_purpose or "",
            project_outcome=row.project_outcome or "",
            project_support_location=row.project_support_location or "",
            is_next_action=bool(row.is_next_action),
            deadline=row.deadline or "",
            parent_project_id=row.parent_project_id,
            parent_project_title=row.parent_project_title or "",
            order=row.order,
        )

    @staticmethod
    def _item_to_row(item: GtdItem) -> GtdItemRow:
        """GtdItemからDBの行を生成する."""
        return GtdItemRow(
            id=item.id,
            user_id=item.user_id,
            title=item.title,
            created_at=item.created_at,
            updated_at=item.updated_at,
            note=item.note,
            item_status=item.item_status.value,
            tag=item.tag.value if item.tag else None,
            status=item.status,
            locations_json=json.dumps([loc.value for loc in item.locations]),
            time_estimate=item.time_estimate.value if item.time_estimate else None,
            energy=item.energy.value if item.energy else None,
            importance=item.importance,
            urgency=item.urgency,
            project_purpose=item.project_purpose,
            project_outcome=item.project_outcome,
            project_support_location=item.project_support_location,
            is_next_action=item.is_next_action,
            deadline=item.deadline,
            parent_project_id=item.parent_project_id,
            parent_project_title=item.parent_project_title,
            order=item.order,
        )
