"""GTDアプリケーションのデータモデル.

すべてのEnum定義とGtdItemデータクラスを提供する。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ItemStatus(StrEnum):
    """Inbox内アイテムの分類状態."""

    INBOX = "inbox"
    SOMEDAY = "someday"
    REFERENCE = "reference"


class Tag(StrEnum):
    """タスクのタグ（明確化フェーズで割当）."""

    DELEGATION = "delegation"
    CALENDAR = "calendar"
    PROJECT = "project"
    DO_NOW = "do_now"
    TASK = "task"


class DelegationStatus(StrEnum):
    """依頼タグの状況."""

    NOT_STARTED = "not_started"
    WAITING = "waiting"
    DONE = "done"


class CalendarStatus(StrEnum):
    """カレンダータグの状況."""

    NOT_STARTED = "not_started"
    REGISTERED = "registered"


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
TAG_STATUS_MAP: dict[
    Tag, type[DelegationStatus | CalendarStatus | DoNowStatus | TaskStatus]
] = {
    Tag.DELEGATION: DelegationStatus,
    Tag.CALENDAR: CalendarStatus,
    Tag.DO_NOW: DoNowStatus,
    Tag.TASK: TaskStatus,
}


def get_status_enum_for_tag(
    tag: Tag,
) -> type[DelegationStatus | CalendarStatus | DoNowStatus | TaskStatus] | None:
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

    Inbox登録からタスク化、完了までのライフサイクルを管理する。

    Attributes:
        id: 一意識別子（UUID）。
        title: アイテムのタイトル。
        created_at: 作成日時（ISO 8601形式）。
        updated_at: 更新日時（ISO 8601形式）。
        item_status: Inbox内の分類状態。
        tag: 明確化フェーズで割り当てられるタグ。
        status: タグごとに異なるステータス値。
        locations: タスク実施場所（タグがTASKの場合のみ、複数選択可）。
        time_estimate: 所要時間の見積もり（タグがTASKの場合のみ）。
        energy: 必要なエネルギーレベル（タグがTASKの場合のみ）。
        importance: 重要度（1-10、タグがPROJECT以外の場合）。
        urgency: 緊急度（1-10、タグがPROJECT以外の場合）。
        parent_project_id: 分解元プロジェクトのID。
        parent_project_title: 分解元プロジェクトのタイトル。
        order: プロジェクト内の順序（0始まり）。
        note: メモ。
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    # 収集フェーズ
    item_status: ItemStatus = ItemStatus.INBOX

    # 明確化フェーズ
    tag: Tag | None = None
    status: str | None = None

    # タスクContext（tag=TASKの場合のみ）
    locations: list[Location] = field(default_factory=list)
    time_estimate: TimeEstimate | None = None
    energy: EnergyLevel | None = None

    # 整理フェーズ（tag!=PROJECTの場合のみ）
    importance: int | None = None
    urgency: int | None = None

    # プロジェクト分解時の親情報
    parent_project_id: str | None = None
    parent_project_title: str = ""
    order: int | None = None

    # メモ
    note: str = ""

    def touch(self) -> None:
        """updated_atを現在時刻に更新する."""
        self.updated_at = _now_iso()

    def is_task(self) -> bool:
        """タスク化済み（タグが割り当てられている）かを返す."""
        return self.tag is not None

    def is_done(self) -> bool:
        """完了状態かを返す."""
        if self.tag is None:
            return False
        status_enum = get_status_enum_for_tag(self.tag)
        if status_enum is None:
            return False
        done_values = {"done"}
        return self.status in done_values

    def needs_organization(self) -> bool:
        """整理（重要度/緊急度設定）が必要かを返す."""
        if self.tag is None or self.tag == Tag.PROJECT:
            return False
        return self.importance is None or self.urgency is None

    def needs_review(self) -> bool:
        """見直し対象かを返す."""
        if self.is_done() or self.tag == Tag.PROJECT:
            return True
        return (
            self.tag == Tag.CALENDAR and self.status == CalendarStatus.REGISTERED.value
        )
