"""収集フェーズのビジネスロジック.

InboxへのItem登録と削除（ゴミ箱移動）を管理する。
エッセンシャル思考に基づき、入力時点で4分類できる場合は直接タグを割り当てる。
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from study_python.gtd.models import (
    DelegationStatus,
    DoNowStatus,
    GtdItem,
    ItemStatus,
    Tag,
    TaskStatus,
)
from study_python.gtd.repository_protocol import GtdRepositoryProtocol


logger = logging.getLogger(__name__)


# タグごとの初期ステータス
_INITIAL_STATUS: dict[Tag, str | None] = {
    Tag.DELEGATION: DelegationStatus.NOT_STARTED.value,
    Tag.PROJECT: None,
    Tag.DO_NOW: DoNowStatus.NOT_STARTED.value,
    Tag.TASK: TaskStatus.NOT_STARTED.value,
}


class CollectionLogic:
    """収集フェーズのロジック.

    Args:
        repository: GTDアイテムリポジトリ。
    """

    def __init__(self, repository: GtdRepositoryProtocol) -> None:
        self._repo = repository

    def add_to_inbox(
        self, title: str, tag: Tag | None = None, note: str = ""
    ) -> GtdItem:
        """Inboxにアイテムを登録する.

        tagが指定された場合は明確化フェーズをスキップして直接分類する。

        Args:
            title: アイテムのタイトル。
            tag: 直接分類する場合のタグ（任意）。
            note: メモ（任意）。

        Returns:
            作成されたアイテム。

        Raises:
            ValueError: タイトルが空または500文字を超える場合。
        """
        if not title.strip():
            msg = "タイトルは必須です"
            raise ValueError(msg)
        if len(title.strip()) > 500:
            msg = "タイトルは500文字以内で入力してください"
            raise ValueError(msg)

        item = GtdItem(title=title.strip(), note=note.strip())
        if tag is not None:
            item.tag = tag
            item.status = _INITIAL_STATUS[tag]
        self._repo.add(item)
        logger.info(f"Added to inbox: '{item.title}' tag={tag} (id={item.id})")
        return item

    def move_to_trash(self, item_id: str) -> GtdItem | None:
        """アイテムをゴミ箱に移動する.

        Args:
            item_id: 削除するアイテムのID。

        Returns:
            ゴミ箱に移動したアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None:
            logger.warning(f"Item not found: {item_id}")
            return None

        item.item_status = ItemStatus.TRASH
        item.deleted_at = datetime.now(tz=UTC).isoformat()
        item.touch()
        logger.info(f"Moved to trash: '{item.title}' (id={item.id})")
        return item

    def get_inbox_items(self) -> list[GtdItem]:
        """Inbox内のアイテムを返す.

        Returns:
            Inboxステータスのアイテムのリスト。
        """
        return self._repo.get_by_status(ItemStatus.INBOX)

    def get_unclassified_inbox_items(self) -> list[GtdItem]:
        """Inbox内の未分類アイテム（タグ未割当）を返す.

        Returns:
            未分類アイテムのリスト。
        """
        return [i for i in self.get_inbox_items() if i.tag is None]

    def reorder_item(self, item_id: str, direction: str) -> bool:
        """同一プロジェクト内でアイテムの順序を上下に移動する.

        Args:
            item_id: 移動するアイテムのID。
            direction: "up" または "down"。

        Returns:
            順序変更が成功した場合True。
        """
        item = self._repo.get(item_id)
        if item is None or item.parent_project_id is None or item.order is None:
            return False

        siblings = sorted(
            [
                i
                for i in self._repo.items
                if i.parent_project_id == item.parent_project_id and i.order is not None
            ],
            key=lambda i: i.order,  # type: ignore[arg-type]
        )

        idx = next((j for j, s in enumerate(siblings) if s.id == item.id), -1)
        if idx < 0:
            return False

        if direction == "up" and idx > 0:
            swap_target = siblings[idx - 1]
        elif direction == "down" and idx < len(siblings) - 1:
            swap_target = siblings[idx + 1]
        else:
            return False

        item.order, swap_target.order = swap_target.order, item.order
        item.touch()
        swap_target.touch()
        return True
