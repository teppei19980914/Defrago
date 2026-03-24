"""SQLAlchemy永続化リポジトリ.

リクエストスコープでインメモリにアイテムを保持し、
flush_to_dbでDB同期する。ロジック層はGtdRepositoryProtocolを通じて利用する。
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
    """SQLAlchemy永続化リポジトリ.

    リクエストごとにDBから全アイテムをメモリに読み込み、
    ロジック層のin-place変更後にflush_to_dbでDB同期する。

    Args:
        session: SQLAlchemyセッション。
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._items: list[GtdItem] = []
        self._load_all()

    def _load_all(self) -> None:
        """全アイテムをDBから読み込む."""
        rows = self._session.query(GtdItemRow).all()
        self._items = [self._row_to_item(r) for r in rows]

    @property
    def items(self) -> list[GtdItem]:
        """全アイテムのリストを返す."""
        return self._items

    def add(self, item: GtdItem) -> None:
        """アイテムを追加する.

        Args:
            item: 追加するアイテム。
        """
        self._items.append(item)

    def remove(self, item_id: str) -> GtdItem | None:
        """アイテムをIDで物理削除する.

        Args:
            item_id: 削除するアイテムのID。

        Returns:
            削除したアイテム。見つからない場合はNone。
        """
        for i, item in enumerate(self._items):
            if item.id == item_id:
                return self._items.pop(i)
        return None

    def get(self, item_id: str) -> GtdItem | None:
        """IDでアイテムを取得する.

        Args:
            item_id: 取得するアイテムのID。

        Returns:
            アイテム。見つからない場合はNone。
        """
        for item in self._items:
            if item.id == item_id:
                return item
        return None

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
        """インメモリ状態をDBに同期する."""
        self._session.query(GtdItemRow).delete()
        for item in self._items:
            self._session.add(self._item_to_row(item))
        self._session.flush()
        logger.debug(f"Flushed {len(self._items)} items to DB")

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
            parent_project_id=row.parent_project_id,
            parent_project_title=row.parent_project_title or "",
            order=row.order,
        )

    @staticmethod
    def _item_to_row(item: GtdItem) -> GtdItemRow:
        """GtdItemからDBの行を生成する."""
        return GtdItemRow(
            id=item.id,
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
            parent_project_id=item.parent_project_id,
            parent_project_title=item.parent_project_title,
            order=item.order,
        )
