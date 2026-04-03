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

    def save_project_plan(
        self,
        item_id: str,
        *,
        purpose: str = "",
        outcome: str = "",
        support_location: str = "",
    ) -> GtdItem | None:
        """プロジェクトの目的・望ましい結果・サポート資料場所を保存する.

        Args:
            item_id: プロジェクトのID。
            purpose: プロジェクトの目的。
            outcome: 望ましい結果。
            support_location: サポート資料の置き場所。

        Returns:
            更新されたアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None or item.tag != Tag.PROJECT:
            return None
        item.project_purpose = purpose
        item.project_outcome = outcome
        item.project_support_location = support_location
        item.touch()
        logger.info(f"Saved project plan: '{item.title}' (id={item.id})")
        return item

    def decompose_project_planned(
        self,
        item_id: str,
        sub_tasks: list[dict[str, str | bool]],
    ) -> list[GtdItem]:
        """計画済みプロジェクトを構造化されたサブタスクに分解する.

        ナチュラル・プランニング・モデルの組織化結果を受け取り、
        サブタスクを生成する。プロジェクトの目的・結果はnoteに記録する。

        Args:
            item_id: 分解するプロジェクトのID。
            sub_tasks: サブタスク情報のリスト。
                各要素: {"title": str, "is_next_action": bool, "deadline": str}

        Returns:
            作成されたサブタスクのリスト。

        Raises:
            ValueError: プロジェクトが見つからない、またはサブタスクが空の場合。
        """
        item = self._repo.get(item_id)
        if item is None:
            msg = f"Item not found: {item_id}"
            raise ValueError(msg)
        if item.tag != Tag.PROJECT:
            msg = f"Item is not a project: {item_id}"
            raise ValueError(msg)
        if not sub_tasks:
            msg = "At least one sub-task is required"
            raise ValueError(msg)

        project_title = item.title
        # プロジェクトの目的・結果をnoteとしてサブタスクに引き継ぐ
        plan_note_parts: list[str] = []
        if item.project_purpose:
            plan_note_parts.append(f"【目的】{item.project_purpose}")
        if item.project_outcome:
            plan_note_parts.append(f"【望ましい結果】{item.project_outcome}")
        if item.project_support_location:
            plan_note_parts.append(f"【資料】{item.project_support_location}")
        plan_note = "\n".join(plan_note_parts)

        new_items: list[GtdItem] = []
        for idx, task_data in enumerate(sub_tasks):
            title = str(task_data.get("title", ""))
            if not title.strip():
                continue
            is_next = bool(task_data.get("is_next_action", False))
            deadline = str(task_data.get("deadline", ""))

            new_item = GtdItem(
                title=title.strip(),
                item_status=ItemStatus.INBOX,
                parent_project_id=item_id,
                parent_project_title=project_title,
                order=idx,
                is_next_action=is_next,
                deadline=deadline,
                note=plan_note,
            )
            self._repo.add(new_item)
            new_items.append(new_item)

        self._repo.remove(item_id)
        logger.info(
            f"Decomposed project '{item.title}' into {len(new_items)} planned sub-tasks"
        )
        return new_items
