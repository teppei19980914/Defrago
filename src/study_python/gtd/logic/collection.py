"""収集フェーズのビジネスロジック.

InboxへのItem登録と分類（削除・参考資料・いつかやる）を管理する。
"""

from __future__ import annotations

import logging

from study_python.gtd.models import GtdItem, ItemStatus
from study_python.gtd.repository_protocol import GtdRepositoryProtocol


logger = logging.getLogger(__name__)


class CollectionLogic:
    """収集フェーズのロジック.

    Args:
        repository: GTDアイテムリポジトリ。
    """

    def __init__(self, repository: GtdRepositoryProtocol) -> None:
        self._repo = repository

    def add_to_inbox(self, title: str, note: str = "") -> GtdItem:
        """InboxにアイテムをItem登録する.

        Args:
            title: アイテムのタイトル。
            note: メモ（任意）。

        Returns:
            作成されたアイテム。

        Raises:
            ValueError: タイトルが空の場合。
        """
        if not title.strip():
            raise ValueError("タイトルは必須です")
        if len(title.strip()) > 500:
            raise ValueError("タイトルは500文字以内で入力してください")

        item = GtdItem(title=title.strip(), note=note.strip())
        self._repo.add(item)
        logger.info(f"Added to inbox: '{item.title}' (id={item.id})")
        return item

    def delete_item(self, item_id: str) -> GtdItem | None:
        """アイテムを物理削除する.

        Args:
            item_id: 削除するアイテムのID。

        Returns:
            削除したアイテム。見つからない場合はNone。
        """
        removed = self._repo.remove(item_id)
        if removed:
            logger.info(f"Deleted item: '{removed.title}' (id={removed.id})")
        return removed

    def move_to_reference(self, item_id: str) -> GtdItem | None:
        """アイテムを参考資料に移動する.

        Args:
            item_id: 移動するアイテムのID。

        Returns:
            更新されたアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None:
            logger.warning(f"Item not found: {item_id}")
            return None

        item.item_status = ItemStatus.REFERENCE
        item.touch()
        logger.info(f"Moved to reference: '{item.title}' (id={item.id})")
        return item

    def move_to_someday(self, item_id: str) -> GtdItem | None:
        """アイテムを「いつかやる」に移動する.

        Args:
            item_id: 移動するアイテムのID。

        Returns:
            更新されたアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None:
            logger.warning(f"Item not found: {item_id}")
            return None

        item.item_status = ItemStatus.SOMEDAY
        item.touch()
        logger.info(f"Moved to someday: '{item.title}' (id={item.id})")
        return item

    def get_inbox_items(self) -> list[GtdItem]:
        """Inbox内のアイテムを返す.

        Returns:
            Inboxステータスのアイテムのリスト。
        """
        return self._repo.get_by_status(ItemStatus.INBOX)

    def process_all_inbox(self) -> int:
        """Inbox内の全アイテムを「いつかやる」に一括移動する.

        Returns:
            移動したアイテム数。
        """
        items = self.get_inbox_items()
        count = 0
        for item in items:
            item.item_status = ItemStatus.SOMEDAY
            item.touch()
            count += 1
        if count > 0:
            logger.info(f"Processed {count} inbox items to someday")
        return count

    def get_someday_items(self) -> list[GtdItem]:
        """「いつかやる」のアイテムを返す.

        Returns:
            Somedayステータスのアイテムのリスト。
        """
        return self._repo.get_by_status(ItemStatus.SOMEDAY)

    def get_reference_items(self) -> list[GtdItem]:
        """参考資料のアイテムを返す.

        Returns:
            Referenceステータスのアイテムのリスト。
        """
        return self._repo.get_by_status(ItemStatus.REFERENCE)

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
