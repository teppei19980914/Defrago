"""実行フェーズのビジネスロジック.

タスクのステータスを変更する（プロジェクトタグを除く）。
"""

from __future__ import annotations

import logging

from study_python.gtd.models import (
    GtdItem,
    Tag,
    get_status_enum_for_tag,
)
from study_python.gtd.repository_protocol import GtdRepositoryProtocol


logger = logging.getLogger(__name__)


class ExecutionLogic:
    """実行フェーズのロジック.

    Args:
        repository: GTDアイテムリポジトリ。
    """

    def __init__(self, repository: GtdRepositoryProtocol) -> None:
        self._repo = repository

    def get_active_tasks(self) -> list[GtdItem]:
        """未完了のタスクを返す（プロジェクト除外）.

        Returns:
            未完了タスクのリスト。
        """
        return [
            item
            for item in self._repo.get_tasks()
            if item.tag != Tag.PROJECT and not item.is_done()
        ]

    def update_status(self, item_id: str, new_status: str) -> GtdItem | None:
        """タスクのステータスを更新する.

        Args:
            item_id: 更新するアイテムのID。
            new_status: 新しいステータス値。

        Returns:
            更新されたアイテム。見つからない場合やプロジェクトの場合はNone。

        Raises:
            ValueError: 無効なステータス値の場合。
        """
        item = self._repo.get(item_id)
        if item is None:
            logger.warning(f"Item not found: {item_id}")
            return None

        if item.tag is None:
            logger.warning(f"Item is not a task: {item_id}")
            return None

        if item.tag == Tag.PROJECT:
            logger.warning(f"Cannot update status on project: {item_id}")
            return None

        status_enum = get_status_enum_for_tag(item.tag)
        if status_enum is None:
            logger.warning(f"No status enum for tag: {item.tag}")
            return None

        # ステータス値のバリデーション
        valid_values = [e.value for e in status_enum]
        if new_status not in valid_values:
            raise ValueError(
                f"無効なステータスです: '{new_status}' (有効な値: {valid_values})"
            )

        item.status = new_status
        item.touch()
        logger.info(f"Updated status to '{new_status}': '{item.title}' (id={item.id})")
        return item

    def get_available_statuses(self, item_id: str) -> list[str] | None:
        """タスクの利用可能なステータス値を返す.

        Args:
            item_id: アイテムのID。

        Returns:
            利用可能なステータス値のリスト。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None or item.tag is None:
            return None

        status_enum = get_status_enum_for_tag(item.tag)
        if status_enum is None:
            return None

        return [e.value for e in status_enum]

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
