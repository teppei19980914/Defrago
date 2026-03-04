"""アプリケーション設定の管理.

ソート設定やその他のアプリケーション設定をJSON永続化する。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from study_python.gtd.models import GtdItem, Tag


logger = logging.getLogger(__name__)

DEFAULT_SETTINGS_DIR = Path.home() / ".mindflow"
DEFAULT_SETTINGS_FILE = "settings.json"


class SortField(StrEnum):
    """ソート対象フィールド."""

    TAG = "tag"
    IMPORTANCE = "importance"
    URGENCY = "urgency"
    STATUS = "status"


class SortDirection(StrEnum):
    """ソート方向."""

    ASCENDING = "ascending"
    DESCENDING = "descending"


# タグのソート順序定義（アクション優先度順）
TAG_SORT_ORDER: dict[str, int] = {
    Tag.DO_NOW.value: 0,
    Tag.DELEGATION.value: 1,
    Tag.CALENDAR.value: 2,
    Tag.TASK.value: 3,
    Tag.PROJECT.value: 4,
}

# ステータスのソート順序定義（進行度順）
STATUS_SORT_ORDER: dict[str, int] = {
    "not_started": 0,
    "in_progress": 1,
    "waiting": 2,
    "registered": 3,
    "done": 4,
}


@dataclass
class SortCriterion:
    """ソート条件の1項目.

    Attributes:
        field: ソート対象フィールド。
        direction: ソート方向（昇順/降順）。
    """

    field: SortField = SortField.URGENCY
    direction: SortDirection = SortDirection.DESCENDING


def default_sort_criteria() -> list[SortCriterion]:
    """デフォルトのソート条件を返す."""
    return [
        SortCriterion(field=SortField.URGENCY, direction=SortDirection.DESCENDING),
        SortCriterion(field=SortField.IMPORTANCE, direction=SortDirection.DESCENDING),
    ]


@dataclass
class AppSettings:
    """アプリケーション設定.

    Attributes:
        sort_criteria: ソート条件のリスト（優先度順）。
        show_done_tasks: 完了タスクを表示するか。
    """

    sort_criteria: list[SortCriterion] = field(default_factory=default_sort_criteria)
    show_done_tasks: bool = False


class SettingsManager:
    """設定の読み書きを管理するロジッククラス.

    Args:
        settings_path: 設定ファイルのパス。Noneの場合はデフォルト。
    """

    def __init__(self, settings_path: Path | None = None) -> None:
        if settings_path is None:
            self._path = DEFAULT_SETTINGS_DIR / DEFAULT_SETTINGS_FILE
        else:
            self._path = settings_path
        self._settings = AppSettings()
        logger.info(f"SettingsManager initialized: {self._path}")

    @property
    def settings_path(self) -> Path:
        """設定ファイルのパスを返す."""
        return self._path

    @property
    def settings(self) -> AppSettings:
        """現在の設定を返す."""
        return self._settings

    def load(self) -> AppSettings:
        """設定ファイルから読み込む.

        Returns:
            読み込んだ設定。ファイルが存在しない場合はデフォルト設定。
        """
        if not self._path.exists():
            logger.info("Settings file not found, using defaults")
            self._settings = AppSettings()
            return self._settings

        try:
            raw = self._path.read_text(encoding="utf-8")
            data = json.loads(raw)
            self._settings = self._dict_to_settings(data)
            logger.info(f"Loaded settings from {self._path}")
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to load settings: {e}")
            self._settings = AppSettings()
        return self._settings

    def save(self) -> None:
        """現在の設定をファイルに保存する."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = self._settings_to_dict(self._settings)
        raw = json.dumps(data, ensure_ascii=False, indent=2)
        self._path.write_text(raw, encoding="utf-8")
        logger.info(f"Saved settings to {self._path}")

    def update_sort_criteria(self, criteria: list[SortCriterion]) -> None:
        """ソート条件を更新する.

        Args:
            criteria: 新しいソート条件リスト。

        Raises:
            ValueError: 条件リストが空の場合、または重複フィールドがある場合。
        """
        if not criteria:
            raise ValueError("ソート条件は1つ以上必要です")

        fields = [c.field for c in criteria]
        if len(fields) != len(set(fields)):
            raise ValueError("同じフィールドが複数指定されています")

        self._settings.sort_criteria = list(criteria)
        logger.info(f"Updated sort criteria: {criteria}")

    def update_show_done_tasks(self, show: bool) -> None:
        """完了タスク表示設定を更新する.

        Args:
            show: 完了タスクを表示するか。
        """
        self._settings.show_done_tasks = show
        logger.info(f"Updated show_done_tasks: {show}")

    def sort_items(self, items: list[GtdItem]) -> list[GtdItem]:
        """設定に基づいてアイテムをソートする.

        Args:
            items: ソート対象のアイテムリスト。

        Returns:
            ソート済みのアイテムリスト（新しいリスト）。
        """
        criteria = self._settings.sort_criteria
        if not criteria:
            return list(items)

        def make_sort_key(item: GtdItem) -> tuple[int, ...]:
            keys: list[int] = []
            for criterion in criteria:
                raw_val = self._get_sort_value(item, criterion.field)
                if criterion.direction == SortDirection.DESCENDING:
                    keys.append(-raw_val)
                else:
                    keys.append(raw_val)
            return tuple(keys)

        return sorted(items, key=make_sort_key)

    @staticmethod
    def _get_sort_value(item: GtdItem, sort_field: SortField) -> int:
        """アイテムからソート用の数値を取得する.

        Args:
            item: ソート対象アイテム。
            sort_field: ソートフィールド。

        Returns:
            ソート用数値。
        """
        if sort_field == SortField.IMPORTANCE:
            return item.importance or 0
        if sort_field == SortField.URGENCY:
            return item.urgency or 0
        if sort_field == SortField.TAG:
            tag_val = item.tag.value if item.tag else ""
            return TAG_SORT_ORDER.get(tag_val, 999)
        if sort_field == SortField.STATUS:
            return STATUS_SORT_ORDER.get(item.status or "", 999)
        return 0  # pragma: no cover

    @staticmethod
    def _settings_to_dict(settings: AppSettings) -> dict[str, object]:
        """AppSettingsを辞書に変換する."""
        return {
            "sort_criteria": [
                {"field": c.field.value, "direction": c.direction.value}
                for c in settings.sort_criteria
            ],
            "show_done_tasks": settings.show_done_tasks,
        }

    @staticmethod
    def _dict_to_settings(data: dict[str, object]) -> AppSettings:
        """辞書からAppSettingsを復元する."""
        raw_criteria = data.get("sort_criteria", [])
        criteria: list[SortCriterion] = []
        if isinstance(raw_criteria, list):
            for c in raw_criteria:
                if isinstance(c, dict):
                    criteria.append(
                        SortCriterion(
                            field=SortField(str(c["field"])),
                            direction=SortDirection(str(c["direction"])),
                        )
                    )

        return AppSettings(
            sort_criteria=criteria if criteria else default_sort_criteria(),
            show_done_tasks=bool(data.get("show_done_tasks", False)),
        )
