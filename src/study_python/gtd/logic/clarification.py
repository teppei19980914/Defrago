"""明確化フェーズのビジネスロジック.

「いつかやる」アイテムをGTD決定木に基づきタスク化する。
"""

from __future__ import annotations

import logging

from study_python.gtd.models import (
    CalendarStatus,
    DelegationStatus,
    DoNowStatus,
    EnergyLevel,
    GtdItem,
    ItemStatus,
    Location,
    Tag,
    TaskStatus,
    TimeEstimate,
)
from study_python.gtd.repository_protocol import GtdRepositoryProtocol


logger = logging.getLogger(__name__)


class ClarificationLogic:
    """明確化フェーズのロジック.

    Args:
        repository: GTDアイテムリポジトリ。
    """

    def __init__(self, repository: GtdRepositoryProtocol) -> None:
        self._repo = repository

    def get_pending_items(self) -> list[GtdItem]:
        """明確化待ちのアイテム（「いつかやる」でタグ未割当）を返す.

        Returns:
            明確化待ちアイテムのリスト。
        """
        return [
            item
            for item in self._repo.get_by_status(ItemStatus.SOMEDAY)
            if item.tag is None
        ]

    def classify_as_delegation(self, item_id: str) -> GtdItem | None:
        """アイテムを「依頼」タグとしてタスク化する.

        自身が実施しなくてもよいアイテムに使用する。

        Args:
            item_id: タスク化するアイテムのID。

        Returns:
            更新されたアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None:
            return None

        item.tag = Tag.DELEGATION
        item.status = DelegationStatus.NOT_STARTED.value
        item.touch()
        logger.info(f"Classified as delegation: '{item.title}' (id={item.id})")
        return item

    def classify_as_calendar(self, item_id: str) -> GtdItem | None:
        """アイテムを「カレンダー」タグとしてタスク化する.

        日時が明確なアイテムに使用する。

        Args:
            item_id: タスク化するアイテムのID。

        Returns:
            更新されたアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None:
            return None

        item.tag = Tag.CALENDAR
        item.status = CalendarStatus.NOT_STARTED.value
        item.touch()
        logger.info(f"Classified as calendar: '{item.title}' (id={item.id})")
        return item

    def classify_as_project(self, item_id: str) -> GtdItem | None:
        """アイテムを「プロジェクト」タグとしてタスク化する.

        2ステップ以上のアクションが必要なアイテムに使用する。

        Args:
            item_id: タスク化するアイテムのID。

        Returns:
            更新されたアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None:
            return None

        item.tag = Tag.PROJECT
        item.status = None
        item.touch()
        logger.info(f"Classified as project: '{item.title}' (id={item.id})")
        return item

    def classify_as_do_now(self, item_id: str) -> GtdItem | None:
        """アイテムを「即実行」タグとしてタスク化する.

        数分で実施可能なアイテムに使用する。

        Args:
            item_id: タスク化するアイテムのID。

        Returns:
            更新されたアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None:
            return None

        item.tag = Tag.DO_NOW
        item.status = DoNowStatus.NOT_STARTED.value
        item.touch()
        logger.info(f"Classified as do_now: '{item.title}' (id={item.id})")
        return item

    def classify_as_task(
        self,
        item_id: str,
        locations: list[Location],
        time_estimate: TimeEstimate,
        energy: EnergyLevel,
    ) -> GtdItem | None:
        """アイテムを「タスク」タグとしてタスク化する.

        Contextも同時に設定する。すべてのContext項目は必須。

        Args:
            item_id: タスク化するアイテムのID。
            locations: 実施場所（1つ以上必須、複数選択可）。
            time_estimate: 所要時間の見積もり（必須）。
            energy: 必要なエネルギーレベル（必須）。

        Returns:
            更新されたアイテム。見つからない場合はNone。

        Raises:
            ValueError: locationsが空の場合。
        """
        if not locations:
            msg = "At least one location is required"
            raise ValueError(msg)

        item = self._repo.get(item_id)
        if item is None:
            return None

        item.tag = Tag.TASK
        item.status = TaskStatus.NOT_STARTED.value
        item.locations = locations
        item.time_estimate = time_estimate
        item.energy = energy
        item.touch()
        logger.info(f"Classified as task: '{item.title}' (id={item.id})")
        return item

    def update_task_context(
        self,
        item_id: str,
        locations: list[Location] | None = None,
        time_estimate: TimeEstimate | None = None,
        energy: EnergyLevel | None = None,
    ) -> GtdItem | None:
        """タスクのContextを更新する.

        Args:
            item_id: 更新するアイテムのID。
            locations: 実施場所（複数選択可）。
            time_estimate: 所要時間の見積もり。
            energy: 必要なエネルギーレベル。

        Returns:
            更新されたアイテム。見つからない場合またはタスクタグでない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None or item.tag != Tag.TASK:
            return None

        if locations is not None:
            item.locations = locations
        if time_estimate is not None:
            item.time_estimate = time_estimate
        if energy is not None:
            item.energy = energy
        item.touch()
        logger.info(f"Updated task context: '{item.title}' (id={item.id})")
        return item
