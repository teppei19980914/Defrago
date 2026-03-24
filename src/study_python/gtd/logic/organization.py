"""整理フェーズのビジネスロジック.

タスクに重要度と緊急度を設定する（プロジェクトタグを除く）。
"""

from __future__ import annotations

import logging

from study_python.gtd.models import GtdItem, Tag
from study_python.gtd.repository_protocol import GtdRepositoryProtocol


logger = logging.getLogger(__name__)

MIN_SCORE = 1
MAX_SCORE = 10


class OrganizationLogic:
    """整理フェーズのロジック.

    Args:
        repository: GTDアイテムリポジトリ。
    """

    def __init__(self, repository: GtdRepositoryProtocol) -> None:
        self._repo = repository

    def get_unorganized_tasks(self) -> list[GtdItem]:
        """重要度/緊急度が未設定のタスクを返す（プロジェクト除外）.

        Returns:
            整理が必要なタスクのリスト。
        """
        return [item for item in self._repo.get_tasks() if item.needs_organization()]

    def set_importance_urgency(
        self,
        item_id: str,
        importance: int,
        urgency: int,
    ) -> GtdItem | None:
        """タスクの重要度と緊急度を設定する.

        Args:
            item_id: 設定するアイテムのID。
            importance: 重要度（1-10）。
            urgency: 緊急度（1-10）。

        Returns:
            更新されたアイテム。見つからない場合やプロジェクトの場合はNone。

        Raises:
            ValueError: 値が範囲外の場合。
        """
        self._validate_score("重要度", importance)
        self._validate_score("緊急度", urgency)

        item = self._repo.get(item_id)
        if item is None:
            logger.warning(f"Item not found: {item_id}")
            return None

        if item.tag == Tag.PROJECT:
            logger.warning(f"Cannot set importance/urgency on project: {item_id}")
            return None

        if item.tag is None:
            logger.warning(f"Item is not a task: {item_id}")
            return None

        item.importance = importance
        item.urgency = urgency
        item.touch()
        logger.info(
            f"Set importance={importance}, urgency={urgency}: "
            f"'{item.title}' (id={item.id})"
        )
        return item

    def get_matrix_quadrants(
        self,
    ) -> dict[str, list[GtdItem]]:
        """重要度×緊急度マトリクスの4象限にタスクを分類する.

        象限の定義:
        - Q1（重要かつ緊急）: importance > 5 AND urgency > 5
        - Q2（重要だが緊急でない）: importance > 5 AND urgency <= 5
        - Q3（緊急だが重要でない）: importance <= 5 AND urgency > 5
        - Q4（重要でも緊急でもない）: importance <= 5 AND urgency <= 5

        Returns:
            象限名をキー、タスクリストを値とする辞書。
        """
        quadrants: dict[str, list[GtdItem]] = {
            "q1_urgent_important": [],
            "q2_not_urgent_important": [],
            "q3_urgent_not_important": [],
            "q4_not_urgent_not_important": [],
        }

        for item in self._repo.get_tasks():
            if item.importance is None or item.urgency is None:
                continue
            if item.tag == Tag.PROJECT:
                continue

            if item.importance > 5 and item.urgency > 5:
                quadrants["q1_urgent_important"].append(item)
            elif item.importance > 5 and item.urgency <= 5:
                quadrants["q2_not_urgent_important"].append(item)
            elif item.importance <= 5 and item.urgency > 5:
                quadrants["q3_urgent_not_important"].append(item)
            else:
                quadrants["q4_not_urgent_not_important"].append(item)

        return quadrants

    @staticmethod
    def _validate_score(name: str, value: int) -> None:
        """スコア値を検証する.

        Args:
            name: フィールド名（エラーメッセージ用）。
            value: 検証する値。

        Raises:
            ValueError: 値が範囲外の場合。
        """
        if not isinstance(value, int) or value < MIN_SCORE or value > MAX_SCORE:
            raise ValueError(
                f"{name}は{MIN_SCORE}から{MAX_SCORE}の整数で指定してください（入力値: {value}）"
            )
