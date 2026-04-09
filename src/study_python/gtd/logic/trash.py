"""ゴミ箱フェーズのビジネスロジック.

削除されたアイテムを30日間保持し、復元または完全削除を管理する。
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from study_python.gtd.models import GtdItem, ItemStatus
from study_python.gtd.repository_protocol import GtdRepositoryProtocol


logger = logging.getLogger(__name__)

RETENTION_DAYS = 30


class TrashLogic:
    """ゴミ箱フェーズのロジック.

    Args:
        repository: GTDアイテムリポジトリ。
    """

    def __init__(self, repository: GtdRepositoryProtocol) -> None:
        self._repo = repository

    def get_trash_items(self) -> list[GtdItem]:
        """ゴミ箱内のアイテムを返す（新しい順）.

        Returns:
            ゴミ箱内アイテムのリスト。
        """
        items = self._repo.get_by_status(ItemStatus.TRASH)
        return sorted(items, key=lambda i: i.deleted_at, reverse=True)

    def restore(self, item_id: str) -> GtdItem | None:
        """アイテムをゴミ箱から復元する.

        v3.1.4 以降、復元先は一律 Inbox の素のアイテム (未分類) となる。
        元がタスクであれプロジェクトであれサブタスクであれ、GTD 関連の状態は
        すべてリセットされ、ユーザーは改めて明確化フェーズで分類し直す必要が
        ある。タイトル・メモ・作成日時など本質的な情報は保持される。

        Args:
            item_id: 復元するアイテムのID。

        Returns:
            復元したアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None or item.item_status != ItemStatus.TRASH:
            return None

        # ゴミ箱状態を解除
        item.item_status = ItemStatus.INBOX
        item.deleted_at = ""

        # 明確化フェーズで設定されるタグ・ステータスをクリア
        item.tag = None
        item.status = None

        # タスク Context をクリア
        item.locations = []
        item.time_estimate = None
        item.energy = None

        # プロジェクト関連の紐づけ・計画情報をクリア
        item.parent_project_id = None
        item.parent_project_title = ""
        item.order = None
        item.project_purpose = ""
        item.project_outcome = ""
        item.project_support_location = ""
        item.is_next_action = False
        item.deadline = ""

        item.touch()
        logger.info(f"Restored from trash to inbox: '{item.title}' (id={item.id})")
        return item

    def delete_permanently(self, item_id: str) -> GtdItem | None:
        """アイテムをゴミ箱から物理削除する.

        Args:
            item_id: 削除するアイテムのID。

        Returns:
            削除したアイテム。見つからない場合はNone。
        """
        item = self._repo.get(item_id)
        if item is None or item.item_status != ItemStatus.TRASH:
            return None

        removed = self._repo.remove(item_id)
        if removed:
            logger.info(f"Permanently deleted: '{removed.title}' (id={removed.id})")
        return removed

    def days_until_auto_delete(self, item: GtdItem) -> int:
        """自動削除までの残り日数を計算する.

        Args:
            item: ゴミ箱内のアイテム。

        Returns:
            残り日数（0以上）。
        """
        if not item.deleted_at:
            return RETENTION_DAYS
        try:
            deleted_at = datetime.fromisoformat(item.deleted_at)
        except ValueError:
            return RETENTION_DAYS
        elapsed = datetime.now(tz=UTC) - deleted_at
        remaining = RETENTION_DAYS - elapsed.days
        return max(0, remaining)
