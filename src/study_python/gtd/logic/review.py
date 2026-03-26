"""見直しフェーズのビジネスロジック.

完了タスクとプロジェクトタスクのレビューを管理する。
"""

from __future__ import annotations

import logging

from study_python.gtd.models import GtdItem, ItemStatus, Tag
from study_python.gtd.repository_protocol import GtdRepositoryProtocol


logger = logging.getLogger(__name__)


class ReviewLogic:
    """見直しフェーズのロジック.

    Args:
        repository: GTDアイテムリポジトリ。
    """

    def __init__(self, repository: GtdRepositoryProtocol) -> None:
        self._repo = repository

    def get_review_items(self) -> list[GtdItem]:
        """見直し対象のアイテムを返す.

        完了タスクとプロジェクトタスクが対象。

        Returns:
            見直し対象アイテムのリスト。
        """
        return [item for item in self._repo.get_tasks() if item.needs_review()]

    def delete_item(self, item_id: str) -> GtdItem | None:
        """アイテムを物理削除する.

        Args:
            item_id: 削除するアイテムのID。

        Returns:
            削除したアイテム。見つからない場合はNone。
        """
        removed = self._repo.remove(item_id)
        if removed:
            logger.info(f"Reviewed and deleted: '{removed.title}' (id={removed.id})")
        return removed

    def move_to_inbox(self, item_id: str) -> GtdItem | None:
        """アイテムをタスクからInboxに戻す.

        タグ、ステータス、Context、重要度/緊急度をリセットする。
        プロジェクトとの紐づけ（parent_project_id, order）は保持する。

        Args:
            item_id: Inboxに戻すアイテムのID。

        Returns:
            更新されたアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None:
            logger.warning(f"Item not found: {item_id}")
            return None

        # タスク情報をリセット（プロジェクト紐づけは保持）
        item.item_status = ItemStatus.INBOX
        item.tag = None
        item.status = None
        item.locations = []
        item.time_estimate = None
        item.energy = None
        item.importance = None
        item.urgency = None
        item.touch()

        logger.info(f"Moved back to inbox: '{item.title}' (id={item.id})")
        return item

    def get_completed_count(self) -> int:
        """完了タスクの数を返す.

        Returns:
            完了タスクの数。
        """
        return sum(1 for item in self._repo.get_tasks() if item.is_done())

    def decompose_project(
        self, item_id: str, sub_task_titles: list[str]
    ) -> list[GtdItem]:
        """プロジェクトを複数のサブタスクに分解してInboxに登録する.

        元のプロジェクトは削除され、各サブタスクが新規Inboxアイテムとして追加される。

        Args:
            item_id: 分解するプロジェクトのID。
            sub_task_titles: サブタスクのタイトルリスト。

        Returns:
            作成されたサブタスクのリスト。

        Raises:
            ValueError: アイテムが見つからない、プロジェクトでない、
                        またはタイトルリストが空の場合。
        """
        item = self._repo.get(item_id)
        if item is None:
            msg = f"Item not found: {item_id}"
            raise ValueError(msg)
        if item.tag != Tag.PROJECT:
            msg = f"Item is not a project: {item_id}"
            raise ValueError(msg)
        if not sub_task_titles:
            msg = "At least one sub-task title is required"
            raise ValueError(msg)

        project_title = item.title
        new_items: list[GtdItem] = []
        for idx, title in enumerate(sub_task_titles):
            new_item = GtdItem(
                title=title,
                item_status=ItemStatus.INBOX,
                parent_project_id=item_id,
                parent_project_title=project_title,
                order=idx,
            )
            self._repo.add(new_item)
            new_items.append(new_item)

        self._repo.remove(item_id)
        logger.info(
            f"Decomposed project '{item.title}' into {len(new_items)} sub-tasks"
        )
        return new_items

    def get_project_count(self) -> int:
        """プロジェクトタスクの数を返す.

        Returns:
            プロジェクトタスクの数。
        """
        return len(self._repo.get_by_tag(Tag.PROJECT))
