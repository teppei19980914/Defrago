"""ダッシュボードウィジェット.

重要度×緊急度マトリクスとサマリー情報を表示する。
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from study_python.gtd.gui.components.matrix_view import MatrixView
from study_python.gtd.gui.styles import COLORS
from study_python.gtd.logic.organization import OrganizationLogic
from study_python.gtd.models import ItemStatus
from study_python.gtd.repository import GtdRepository


logger = logging.getLogger(__name__)


class DashboardWidget(QWidget):
    """ダッシュボードウィジェット."""

    def __init__(
        self, repository: GtdRepository, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._repo = repository
        self._org_logic = OrganizationLogic(repository)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # タイトル
        title = QLabel("ダッシュボード")
        title.setProperty("heading", True)
        layout.addWidget(title)

        # サマリーカード行
        self._summary_layout = QHBoxLayout()
        self._summary_layout.setSpacing(12)
        self._summary_cards: dict[str, QLabel] = {}

        card_defs = [
            ("inbox", "Inbox", COLORS["accent_blue"]),
            ("tasks", "タスク", COLORS["accent_green"]),
            ("done", "完了", COLORS["accent_mauve"]),
            ("q1", "緊急×重要", COLORS["q1_color"]),
        ]

        for key, label_text, color in card_defs:
            card = self._create_summary_card(label_text, "0", color)
            self._summary_cards[key] = card
            self._summary_layout.addWidget(card)

        layout.addLayout(self._summary_layout)

        # マトリクスビュー
        self._matrix_view = MatrixView()
        layout.addWidget(self._matrix_view, 1)

    def _create_summary_card(self, label: str, value: str, color: str) -> QLabel:
        """サマリーカードを作成する."""
        card = QLabel(f"{value}\n{label}")
        card.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card.setStyleSheet(
            f"""
            background-color: {COLORS["bg_secondary"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            padding: 16px;
            font-size: 14px;
            border-left: 4px solid {color};
            """
        )
        card.setMinimumHeight(70)
        return card

    def refresh(self) -> None:
        """表示を更新する."""
        inbox_count = len(self._repo.get_by_status(ItemStatus.INBOX))
        tasks = self._repo.get_tasks()
        active_count = sum(1 for t in tasks if not t.is_done())
        done_count = sum(1 for t in tasks if t.is_done())

        quadrants = self._org_logic.get_matrix_quadrants()
        q1_count = len(quadrants["q1_urgent_important"])

        self._summary_cards["inbox"].setText(f"{inbox_count}\nInbox")
        self._summary_cards["tasks"].setText(f"{active_count}\nタスク")
        self._summary_cards["done"].setText(f"{done_count}\n完了")
        self._summary_cards["q1"].setText(f"{q1_count}\n緊急×重要")

        # マトリクスにタスクを設定
        scored_items = [
            item
            for item in tasks
            if item.importance is not None and item.urgency is not None
        ]
        self._matrix_view.set_items(scored_items)
