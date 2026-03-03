"""アイテムカードコンポーネント.

GTDアイテムを表示するカードウィジェットを提供する。
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from study_python.gtd.gui.styles import (
    COLORS,
    STATUS_DISPLAY_NAMES,
    TAG_COLORS,
    TAG_DISPLAY_NAMES,
)
from study_python.gtd.models import GtdItem


logger = logging.getLogger(__name__)


class ItemCard(QWidget):
    """GTDアイテムを表示するカードウィジェット.

    Signals:
        action_triggered: アクションボタンがクリックされた時に発火。(item_id, action_name)
    """

    action_triggered = Signal(str, str)

    def __init__(
        self,
        item: GtdItem,
        actions: list[tuple[str, str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """カードを初期化する.

        Args:
            item: 表示するGtdItem。
            actions: アクションボタンのリスト。[(action_name, display_text), ...]
            parent: 親ウィジェット。
        """
        super().__init__(parent)
        self._item = item
        self._actions = actions or []
        self._setup_ui()

    @property
    def item(self) -> GtdItem:
        """表示中のアイテムを返す."""
        return self._item

    def _setup_ui(self) -> None:
        """UIを構築する."""
        self.setStyleSheet(
            f"""
            ItemCard {{
                background-color: {COLORS["bg_secondary"]};
                border: 1px solid {COLORS["border"]};
                border-radius: 8px;
            }}
            """
        )
        self.setContentsMargins(12, 10, 12, 10)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # ヘッダー行: タイトル + タグバッジ
        header = QHBoxLayout()
        header.setSpacing(8)

        title_label = QLabel(self._item.title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header.addWidget(title_label)

        if self._item.tag is not None:
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
            header.addWidget(tag_badge)

        header.addStretch()

        # ステータス表示
        if self._item.status is not None:
            status_name = STATUS_DISPLAY_NAMES.get(self._item.status, self._item.status)
            status_label = QLabel(status_name)
            status_label.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 12px;"
            )
            header.addWidget(status_label)

        layout.addLayout(header)

        # 重要度/緊急度バッジ（設定されている場合）
        if self._item.importance is not None and self._item.urgency is not None:
            score_label = QLabel(
                f"重要度: {self._item.importance}  緊急度: {self._item.urgency}"
            )
            score_label.setStyleSheet(
                f"color: {COLORS['text_muted']}; font-size: 11px;"
            )
            layout.addWidget(score_label)

        # メモ表示（あれば）
        if self._item.note:
            note_label = QLabel(self._item.note)
            note_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
            note_label.setWordWrap(True)
            layout.addWidget(note_label)

        # アクションボタン行
        if self._actions:
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(6)
            btn_layout.addStretch()

            for action_name, display_text in self._actions:
                btn = QPushButton(display_text)
                btn.setFixedHeight(28)
                if action_name == "delete":
                    btn.setProperty("danger", True)
                else:
                    btn.setProperty("secondary", True)
                btn.clicked.connect(
                    lambda checked, a=action_name: self.action_triggered.emit(
                        self._item.id, a
                    )
                )
                btn_layout.addWidget(btn)

            layout.addLayout(btn_layout)
