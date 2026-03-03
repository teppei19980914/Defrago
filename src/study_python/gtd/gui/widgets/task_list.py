"""タスク一覧・実行フェーズウィジェット.

未完了タスクの一覧表示とステータス変更を行うUI。
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from study_python.gtd.gui.styles import (
    COLORS,
    STATUS_DISPLAY_NAMES,
    TAG_COLORS,
    TAG_DISPLAY_NAMES,
)
from study_python.gtd.logic.execution import ExecutionLogic
from study_python.gtd.models import GtdItem, Tag, get_status_enum_for_tag
from study_python.gtd.repository import GtdRepository


logger = logging.getLogger(__name__)


class TaskRow(QWidget):
    """タスク行ウィジェット."""

    status_changed = Signal(str, str)  # item_id, new_status

    def __init__(self, item: GtdItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._item = item
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setStyleSheet(
            f"""
            TaskRow {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 8px;
            }}
            """
        )
        self.setContentsMargins(12, 8, 12, 8)

        layout = QHBoxLayout(self)
        layout.setSpacing(12)

        # タグバッジ
        if self._item.tag:
            tag_name = TAG_DISPLAY_NAMES.get(self._item.tag.value, self._item.tag.value)
            tag_color = TAG_COLORS.get(self._item.tag.value, COLORS["accent_blue"])
            tag_badge = QLabel(tag_name)
            tag_badge.setStyleSheet(
                f"""
                background-color: {tag_color};
                color: {COLORS["bg_primary"]};
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
                """
            )
            tag_badge.setFixedWidth(80)
            layout.addWidget(tag_badge)

        # タイトル
        title = QLabel(self._item.title)
        title.setStyleSheet("font-size: 14px;")
        layout.addWidget(title, 1)

        # 重要度/緊急度
        if self._item.importance is not None and self._item.urgency is not None:
            score = QLabel(f"重{self._item.importance} 緊{self._item.urgency}")
            score.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
            layout.addWidget(score)

        # ステータスコンボボックス
        if self._item.tag and self._item.tag != Tag.PROJECT:
            status_enum = get_status_enum_for_tag(self._item.tag)
            if status_enum:
                self._status_combo = QComboBox()
                for s in status_enum:
                    display = STATUS_DISPLAY_NAMES.get(s.value, s.value)
                    self._status_combo.addItem(display, s.value)

                # 現在のステータスを選択
                if self._item.status:
                    for i in range(self._status_combo.count()):
                        if self._status_combo.itemData(i) == self._item.status:
                            self._status_combo.setCurrentIndex(i)
                            break

                self._status_combo.currentIndexChanged.connect(self._on_status_changed)
                layout.addWidget(self._status_combo)

    def _on_status_changed(self, index: int) -> None:
        """ステータス変更ハンドラ."""
        new_status = self._status_combo.itemData(index)
        if new_status and new_status != self._item.status:
            self.status_changed.emit(self._item.id, str(new_status))


class TaskListWidget(QWidget):
    """タスク一覧・実行フェーズウィジェット.

    Signals:
        data_changed: データが変更された時に発火。
    """

    data_changed = Signal()

    def __init__(
        self, repository: GtdRepository, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._repo = repository
        self._logic = ExecutionLogic(repository)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        # タイトル行
        header = QHBoxLayout()
        title = QLabel("実行 - タスク一覧")
        title.setProperty("heading", True)
        header.addWidget(title)
        header.addStretch()

        # フィルター
        header.addWidget(QLabel("フィルタ:"))
        self._filter_combo = QComboBox()
        self._filter_combo.addItem("すべて", "all")
        self._filter_combo.addItem("依頼", Tag.DELEGATION.value)
        self._filter_combo.addItem("カレンダー", Tag.CALENDAR.value)
        self._filter_combo.addItem("即実行", Tag.DO_NOW.value)
        self._filter_combo.addItem("タスク", Tag.TASK.value)
        self._filter_combo.currentIndexChanged.connect(lambda _: self.refresh())
        header.addWidget(self._filter_combo)

        layout.addLayout(header)

        self._count_label = QLabel("")
        self._count_label.setProperty("muted", True)
        layout.addWidget(self._count_label)

        # タスクリスト
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        layout.addWidget(scroll, 1)

    def _on_status_changed(self, item_id: str, new_status: str) -> None:
        """ステータス変更ハンドラ."""
        try:
            self._logic.update_status(item_id, new_status)
            self.data_changed.emit()
        except ValueError as e:
            logger.error(f"Status update failed: {e}")

    def refresh(self) -> None:
        """表示を更新する."""
        # 既存行をクリア
        while self._list_layout.count() > 1:
            child = self._list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # フィルタ
        filter_val = self._filter_combo.currentData()
        tasks = self._logic.get_active_tasks()

        if filter_val != "all":
            tasks = [t for t in tasks if t.tag and t.tag.value == filter_val]

        # 優先度順ソート（重要度×緊急度 降順）
        def sort_key(item: GtdItem) -> tuple[int, int]:
            imp = item.importance or 0
            urg = item.urgency or 0
            return (-imp, -urg)

        tasks.sort(key=sort_key)

        self._count_label.setText(f"{len(tasks)} 件のタスク")

        for item in tasks:
            row = TaskRow(item, parent=self._list_container)
            row.status_changed.connect(self._on_status_changed)
            self._list_layout.insertWidget(self._list_layout.count() - 1, row)
