"""GTDアプリケーションのデータモデル.

すべてのEnum定義とGtdItemデータクラスを提供する。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ItemStatus(StrEnum):
    """アイテムの状態."""

    INBOX = "inbox"
    SOMEDAY = "someday"
    REFERENCE = "reference"
    TRASH = "trash"


class Tag(StrEnum):
    """タスクのタグ（明確化フェーズで割当）.

    エッセンシャル思考に基づき4分類で構成される。
    """

    DELEGATION = "delegation"
    PROJECT = "project"
    DO_NOW = "do_now"
    TASK = "task"


class DelegationStatus(StrEnum):
    """委任タグの状況."""

    NOT_STARTED = "not_started"
    WAITING = "waiting"
    DONE = "done"


class DoNowStatus(StrEnum):
    """即実行タグの状況."""

    NOT_STARTED = "not_started"
    DONE = "done"


class TaskStatus(StrEnum):
    """タスクタグの状況."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Location(StrEnum):
    """タスク実施場所."""

    DESK = "desk"
    HOME = "home"
    COMMUTE = "commute"


class TimeEstimate(StrEnum):
    """タスク所要時間の見積もり."""

    WITHIN_10MIN = "10min"
    WITHIN_30MIN = "30min"
    WITHIN_1HOUR = "1hour"


class EnergyLevel(StrEnum):
    """タスクに必要なエネルギーレベル."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# タグごとのステータスEnumマッピング
TAG_STATUS_MAP: dict[Tag, type[DelegationStatus | DoNowStatus | TaskStatus]] = {
    Tag.DELEGATION: DelegationStatus,
    Tag.DO_NOW: DoNowStatus,
    Tag.TASK: TaskStatus,
}


def get_status_enum_for_tag(
    tag: Tag,
) -> type[DelegationStatus | DoNowStatus | TaskStatus] | None:
    """タグに対応するステータスEnumクラスを返す.

    Args:
        tag: タスクのタグ。

    Returns:
        対応するステータスEnumクラス。プロジェクトの場合はNone。
    """
    return TAG_STATUS_MAP.get(tag)


def _now_iso() -> str:
    """現在時刻をISO 8601形式の文字列で返す."""
    return datetime.now(tz=UTC).isoformat()


@dataclass
class GtdItem:
    """GTDアイテムのデータモデル.

    Inbox登録から分類、実行、見直しまでのライフサイクルを管理する。
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    title: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    # アイテムの状態
    item_status: ItemStatus = ItemStatus.INBOX

    # 明確化フェーズで設定されるタグ
    tag: Tag | None = None
    status: str | None = None

    # タスクContext（tag=TASKの場合のみ）
    locations: list[Location] = field(default_factory=list)
    time_estimate: TimeEstimate | None = None
    energy: EnergyLevel | None = None

    # プロジェクト分解時の親情報
    parent_project_id: str | None = None
    parent_project_title: str = ""
    order: int | None = None

    # プロジェクト計画（ナチュラル・プランニング・モデル）
    project_purpose: str = ""
    project_outcome: str = ""
    project_support_location: str = ""
    is_next_action: bool = False
    deadline: str = ""

    # ゴミ箱移動日時（item_status=TRASH時のみ設定）
    deleted_at: str = ""

    # メモ
    note: str = ""

    def touch(self) -> None:
        """updated_atを現在時刻に更新する."""
        self.updated_at = _now_iso()

    def is_classified(self) -> bool:
        """分類済み（タグが割り当てられている）かを返す."""
        return self.tag is not None

    def is_done(self) -> bool:
        """完了状態かを返す."""
        if self.tag is None:
            return False
        status_enum = get_status_enum_for_tag(self.tag)
        if status_enum is None:
            return False
        return self.status == "done"

    def needs_review(self) -> bool:
        """見直し対象かを返す."""
        if self.item_status == ItemStatus.TRASH:
            return False
        return self.is_done() or self.tag == Tag.PROJECT

    def is_in_trash(self) -> bool:
        """ゴミ箱内のアイテムかを返す."""
        return self.item_status == ItemStatus.TRASH
