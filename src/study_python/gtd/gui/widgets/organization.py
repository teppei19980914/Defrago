"""整理フェーズウィジェット.

タスクに重要度と緊急度を設定するUI。
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from study_python.gtd.gui.components.matrix_view import MatrixView
from study_python.gtd.gui.styles import COLORS, TAG_COLORS, TAG_DISPLAY_NAMES
from study_python.gtd.logic.organization import OrganizationLogic
from study_python.gtd.models import GtdItem
from study_python.gtd.repository import GtdRepository


logger = logging.getLogger(__name__)


class OrganizationWidget(QWidget):
    """整理フェーズウィジェット.

    Signals:
        data_changed: データが変更された時に発火。
    """

    data_changed = Signal()

    def __init__(
        self, repository: GtdRepository, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._repo = repository
        self._logic = OrganizationLogic(repository)
        self._current_item: GtdItem | None = None
        self._pending_items: list[GtdItem] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QHBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # 左パネル: 評価UI
        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)

        title = QLabel("整理 - 重要度×緊急度")
        title.setProperty("heading", True)
        left_panel.addWidget(title)

        self._progress_label = QLabel("")
        self._progress_label.setProperty("muted", True)
        left_panel.addWidget(self._progress_label)

        # アイテム表示
        self._item_display = QLabel("")
        self._item_display.setStyleSheet(
            f"""
            background-color: {COLORS["bg_secondary"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            padding: 16px;
            font-size: 16px;
            font-weight: bold;
            """
        )
        self._item_display.setWordWrap(True)
        left_panel.addWidget(self._item_display)

        # タグバッジ
        self._tag_label = QLabel("")
        left_panel.addWidget(self._tag_label)

        # 重要度スライダー
        importance_header = QHBoxLayout()
        importance_header.addWidget(QLabel("重要度:"))
        self._importance_value = QLabel("5")
        self._importance_value.setStyleSheet("font-weight: bold; font-size: 16px;")
        importance_header.addWidget(self._importance_value)
        importance_header.addStretch()
        left_panel.addLayout(importance_header)

        self._importance_slider = QSlider(Qt.Orientation.Horizontal)
        self._importance_slider.setRange(1, 10)
        self._importance_slider.setValue(5)
        self._importance_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._importance_slider.setTickInterval(1)
        self._importance_slider.valueChanged.connect(
            lambda v: self._importance_value.setText(str(v))
        )
        left_panel.addWidget(self._importance_slider)

        imp_labels = QHBoxLayout()
        imp_labels.addWidget(QLabel("低"))
        imp_labels.addStretch()
        imp_labels.addWidget(QLabel("高"))
        left_panel.addLayout(imp_labels)

        # 緊急度スライダー
        urgency_header = QHBoxLayout()
        urgency_header.addWidget(QLabel("緊急度:"))
        self._urgency_value = QLabel("5")
        self._urgency_value.setStyleSheet("font-weight: bold; font-size: 16px;")
        urgency_header.addWidget(self._urgency_value)
        urgency_header.addStretch()
        left_panel.addLayout(urgency_header)

        self._urgency_slider = QSlider(Qt.Orientation.Horizontal)
        self._urgency_slider.setRange(1, 10)
        self._urgency_slider.setValue(5)
        self._urgency_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._urgency_slider.setTickInterval(1)
        self._urgency_slider.valueChanged.connect(
            lambda v: self._urgency_value.setText(str(v))
        )
        left_panel.addWidget(self._urgency_slider)

        urg_labels = QHBoxLayout()
        urg_labels.addWidget(QLabel("低"))
        urg_labels.addStretch()
        urg_labels.addWidget(QLabel("高"))
        left_panel.addLayout(urg_labels)

        # 設定ボタン
        set_btn = QPushButton("設定して次へ")
        set_btn.clicked.connect(self._on_set)
        left_panel.addWidget(set_btn)

        # 空メッセージ
        self._empty_label = QLabel("評価するタスクはありません")
        self._empty_label.setProperty("subheading", True)
        self._empty_label.setVisible(False)
        left_panel.addWidget(self._empty_label)

        left_panel.addStretch()

        left_container = QWidget()
        left_container.setLayout(left_panel)
        left_container.setMaximumWidth(500)
        layout.addWidget(left_container)

        # 右パネル: マトリクスプレビュー
        right_panel = QVBoxLayout()
        preview_label = QLabel("マトリクスプレビュー")
        preview_label.setProperty("subheading", True)
        right_panel.addWidget(preview_label)

        self._matrix_view = MatrixView()
        right_panel.addWidget(self._matrix_view, 1)

        right_container = QWidget()
        right_container.setLayout(right_panel)
        layout.addWidget(right_container, 1)

    def _on_set(self) -> None:
        """設定ボタンのハンドラ."""
        if self._current_item is None:
            return

        importance = self._importance_slider.value()
        urgency = self._urgency_slider.value()

        self._logic.set_importance_urgency(self._current_item.id, importance, urgency)

        self.data_changed.emit()
        self._advance_to_next_item()

    def _advance_to_next_item(self) -> None:
        """次のアイテムに進む."""
        self._pending_items = self._logic.get_unorganized_tasks()
        self._update_matrix_preview()

        if self._pending_items:
            self._current_item = self._pending_items[0]
            self._show_current_item()
        else:
            self._current_item = None
            self._item_display.setText("")
            self._tag_label.setText("")
            self._empty_label.setVisible(True)
            self._progress_label.setText("")

    def _show_current_item(self) -> None:
        """現在のアイテム情報を表示する."""
        if self._current_item is None:
            return
        self._item_display.setText(self._current_item.title)
        self._empty_label.setVisible(False)

        # タグバッジ
        if self._current_item.tag:
            tag_name = TAG_DISPLAY_NAMES.get(
                self._current_item.tag.value, self._current_item.tag.value
            )
            tag_color = TAG_COLORS.get(
                self._current_item.tag.value, COLORS["accent_blue"]
            )
            self._tag_label.setStyleSheet(
                f"""
                background-color: {tag_color};
                color: {COLORS["bg_primary"]};
                padding: 2px 12px;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                max-width: 100px;
                """
            )
            self._tag_label.setText(tag_name)

        idx = self._pending_items.index(self._current_item) + 1
        total = len(self._pending_items)
        self._progress_label.setText(f"{idx} / {total} 件")

        # スライダーリセット
        self._importance_slider.setValue(5)
        self._urgency_slider.setValue(5)

    def _update_matrix_preview(self) -> None:
        """マトリクスプレビューを更新する."""
        tasks = self._repo.get_tasks()
        scored = [
            item
            for item in tasks
            if item.importance is not None and item.urgency is not None
        ]
        self._matrix_view.set_items(scored)

    def refresh(self) -> None:
        """表示を更新する."""
        self._pending_items = self._logic.get_unorganized_tasks()
        self._update_matrix_preview()

        if self._pending_items:
            self._current_item = self._pending_items[0]
            self._show_current_item()
            self._empty_label.setVisible(False)
        else:
            self._current_item = None
            self._item_display.setText("")
            self._tag_label.setText("")
            self._empty_label.setVisible(True)
            self._progress_label.setText("")
