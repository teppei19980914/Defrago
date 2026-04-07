"""明確化フェーズのビジネスロジック.

エッセンシャル思考に基づき、Inboxアイテムを4つのタグに分類する:
- 委任 (DELEGATION): 他の人でもできる
- プロジェクト (PROJECT): 複数のアクションが必要
- 即実行 (DO_NOW): 今この場でできる（環境・状況不問）
- タスク (TASK): 環境や状況が揃う必要がある
"""

from __future__ import annotations

import logging

from study_python.gtd.models import (
    DelegationStatus,
    DoNowStatus,
    EnergyLevel,
    GtdItem,
    ItemStatus,
    Location,
    Tag,
    TaskStatus,
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
        """明確化待ちのアイテム（Inbox内でタグ未割当）を返す.

        Returns:
            明確化待ちアイテムのリスト（古い順）。
        """
        items = [
            item
            for item in self._repo.get_by_status(ItemStatus.INBOX)
            if item.tag is None
        ]
        return sorted(items, key=lambda i: i.created_at)

    def classify_as_delegation(self, item_id: str) -> GtdItem | None:
        """アイテムを「委任」タグとして分類する.

        他の人でもできるアイテムに使用する。

        Args:
            item_id: 分類するアイテムのID。

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

    def classify_as_project(self, item_id: str) -> GtdItem | None:
        """アイテムを「プロジェクト」タグとして分類する.

        複数のアクションが必要なアイテムに使用する。

        Args:
            item_id: 分類するアイテムのID。

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
        """アイテムを「即実行」タグとして分類する.

        今この場でできる（環境・状況不問の）アイテムに使用する。

        Args:
            item_id: 分類するアイテムのID。

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

    def classify_as_task(self, item_id: str) -> GtdItem | None:
        """アイテムを「タスク」タグとして分類する.

        環境や状況が揃う必要があるアイテムに使用する。
        Contextは未設定状態となり、後で実行画面から設定できる。

        Args:
            item_id: 分類するアイテムのID。

        Returns:
            更新されたアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None:
            return None

        item.tag = Tag.TASK
        item.status = TaskStatus.NOT_STARTED.value
        item.touch()
        logger.info(f"Classified as task: '{item.title}' (id={item.id})")
        return item

    def update_task_context(
        self,
        item_id: str,
        locations: list[Location] | None = None,
        time_estimate: object | None = None,
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
            item.time_estimate = time_estimate  # type: ignore[assignment]
        if energy is not None:
            item.energy = energy
        item.touch()
        logger.info(f"Updated task context: '{item.title}' (id={item.id})")
        return item
