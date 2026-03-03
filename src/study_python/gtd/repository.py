"""GTDアイテムのJSON永続化レイヤー.

GtdItemのリストをJSONファイルに読み書きする。
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path

from study_python.gtd.models import (
    EnergyLevel,
    GtdItem,
    ItemStatus,
    Location,
    Tag,
    TimeEstimate,
)


logger = logging.getLogger(__name__)

DEFAULT_DATA_DIR = Path.home() / ".mindflow"
DEFAULT_DATA_FILE = "gtd_data.json"


class GtdRepository:
    """GTDアイテムのJSON永続化リポジトリ.

    Args:
        data_path: JSONデータファイルのパス。Noneの場合はデフォルトパス。
    """

    def __init__(self, data_path: Path | None = None) -> None:
        if data_path is None:
            self._data_path = DEFAULT_DATA_DIR / DEFAULT_DATA_FILE
        else:
            self._data_path = data_path
        self._items: list[GtdItem] = []
        logger.info(f"Repository initialized: {self._data_path}")

    @property
    def data_path(self) -> Path:
        """データファイルのパスを返す."""
        return self._data_path

    @property
    def items(self) -> list[GtdItem]:
        """全アイテムのリストを返す."""
        return self._items

    def load(self) -> list[GtdItem]:
        """JSONファイルからアイテムを読み込む.

        Returns:
            読み込んだアイテムのリスト。

        Raises:
            json.JSONDecodeError: JSONのパースに失敗した場合（ログ出力後に空リスト返却）。
        """
        if not self._data_path.exists():
            logger.info("Data file not found, starting with empty list")
            self._items = []
            return self._items

        try:
            raw = self._data_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            self._items = [self._dict_to_item(d) for d in data]
            logger.info(f"Loaded {len(self._items)} items from {self._data_path}")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(f"Failed to load data: {e}")
            self._items = []
        return self._items

    def save(self) -> None:
        """現在のアイテムをJSONファイルに保存する."""
        self._data_path.parent.mkdir(parents=True, exist_ok=True)
        data = [self._item_to_dict(item) for item in self._items]
        raw = json.dumps(data, ensure_ascii=False, indent=2)
        self._data_path.write_text(raw, encoding="utf-8")
        logger.info(f"Saved {len(self._items)} items to {self._data_path}")

    def add(self, item: GtdItem) -> None:
        """アイテムを追加する.

        Args:
            item: 追加するアイテム。
        """
        self._items.append(item)
        logger.debug(f"Added item: {item.id} '{item.title}'")

    def remove(self, item_id: str) -> GtdItem | None:
        """アイテムをIDで物理削除する.

        Args:
            item_id: 削除するアイテムのID。

        Returns:
            削除したアイテム。見つからない場合はNone。
        """
        for i, item in enumerate(self._items):
            if item.id == item_id:
                removed = self._items.pop(i)
                logger.debug(f"Removed item: {removed.id} '{removed.title}'")
                return removed
        logger.warning(f"Item not found for removal: {item_id}")
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
        return [item for item in self._items if item.item_status == status]

    def get_by_tag(self, tag: Tag) -> list[GtdItem]:
        """タグでフィルタリングしたアイテムを返す.

        Args:
            tag: フィルタ条件のTag。

        Returns:
            該当するアイテムのリスト。
        """
        return [item for item in self._items if item.tag == tag]

    def get_tasks(self) -> list[GtdItem]:
        """タスク化済み（タグが割り当てられている）アイテムを返す.

        Returns:
            タスク化済みアイテムのリスト。
        """
        return [item for item in self._items if item.is_task()]

    @staticmethod
    def _item_to_dict(item: GtdItem) -> dict[str, object]:
        """GtdItemを辞書に変換する."""
        d = asdict(item)
        # Enum値を文字列に変換
        d["item_status"] = item.item_status.value
        d["tag"] = item.tag.value if item.tag else None
        d["locations"] = [loc.value for loc in item.locations]
        d["time_estimate"] = item.time_estimate.value if item.time_estimate else None
        d["energy"] = item.energy.value if item.energy else None
        return d

    @staticmethod
    def _dict_to_item(d: dict[str, object]) -> GtdItem:
        """辞書からGtdItemを復元する."""
        return GtdItem(
            id=str(d["id"]),
            title=str(d["title"]),
            created_at=str(d["created_at"]),
            updated_at=str(d["updated_at"]),
            item_status=ItemStatus(str(d["item_status"])),
            tag=Tag(str(d["tag"])) if d.get("tag") else None,
            status=str(d["status"]) if d.get("status") else None,
            locations=[Location(str(loc)) for loc in d.get("locations", [])],  # type: ignore[union-attr]
            time_estimate=TimeEstimate(str(d["time_estimate"]))
            if d.get("time_estimate")
            else None,
            energy=EnergyLevel(str(d["energy"])) if d.get("energy") else None,
            importance=int(d["importance"])
            if d.get("importance") is not None
            else None,  # type: ignore[arg-type]
            urgency=int(d["urgency"]) if d.get("urgency") is not None else None,  # type: ignore[arg-type]
            note=str(d.get("note", "")),
        )
