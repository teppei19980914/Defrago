"""整理フェーズウィジェット.

タスクに重要度と緊急度を設定するUI。
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent, QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
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


class OrganizationDialog(QDialog):
    """整理フェーズの強制モーダルダイアログ.

    全アイテムの重要度・緊急度設定が完了するまで閉じられない。
    """

    def __init__(
        self,
        items: list[GtdItem],
        logic: OrganizationLogic,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._items = list(items)
        self._logic = logic
        self._current_index = 0
        self.setWindowTitle("整理 - 重要度×緊急度の設定")
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_primary']}; }}")
        # 閉じるボタンを無効化
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        self._setup_ui()
        self._show_current_item()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        heading = QLabel("重要度×緊急度を設定")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        desc = QLabel("すべてのアイテムに重要度と緊急度を設定してください")
        desc.setProperty("subheading", True)
        layout.addWidget(desc)

        self._progress_label = QLabel("")
        self._progress_label.setProperty("muted", True)
        layout.addWidget(self._progress_label)

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
        layout.addWidget(self._item_display)

        # タグバッジ
        self._tag_label = QLabel("")
        layout.addWidget(self._tag_label)

        # 重要度スライダー
        importance_header = QHBoxLayout()
        importance_header.addWidget(QLabel("重要度:"))
        self._importance_value = QLabel("5")
        self._importance_value.setStyleSheet("font-weight: bold; font-size: 16px;")
        importance_header.addWidget(self._importance_value)
        importance_header.addStretch()
        layout.addLayout(importance_header)

        self._importance_slider = QSlider(Qt.Orientation.Horizontal)
        self._importance_slider.setRange(1, 10)
        self._importance_slider.setValue(5)
        self._importance_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._importance_slider.setTickInterval(1)
        self._importance_slider.valueChanged.connect(
            lambda v: self._importance_value.setText(str(v))
        )
        layout.addWidget(self._importance_slider)

        imp_labels = QHBoxLayout()
        imp_labels.addWidget(QLabel("低"))
        imp_labels.addStretch()
        imp_labels.addWidget(QLabel("高"))
        layout.addLayout(imp_labels)

        # 緊急度スライダー
        urgency_header = QHBoxLayout()
        urgency_header.addWidget(QLabel("緊急度:"))
        self._urgency_value = QLabel("5")
        self._urgency_value.setStyleSheet("font-weight: bold; font-size: 16px;")
        urgency_header.addWidget(self._urgency_value)
        urgency_header.addStretch()
        layout.addLayout(urgency_header)

        self._urgency_slider = QSlider(Qt.Orientation.Horizontal)
        self._urgency_slider.setRange(1, 10)
        self._urgency_slider.setValue(5)
        self._urgency_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._urgency_slider.setTickInterval(1)
        self._urgency_slider.valueChanged.connect(
            lambda v: self._urgency_value.setText(str(v))
        )
        layout.addWidget(self._urgency_slider)

        urg_labels = QHBoxLayout()
        urg_labels.addWidget(QLabel("低"))
        urg_labels.addStretch()
        urg_labels.addWidget(QLabel("高"))
        layout.addLayout(urg_labels)

        # 設定ボタン
        self._set_btn = QPushButton("設定して次へ")
        self._set_btn.clicked.connect(self._on_set)
        layout.addWidget(self._set_btn)

    def _show_current_item(self) -> None:
        """現在のアイテムを表示する."""
        item = self._items[self._current_index]
        self._item_display.setText(item.title)

        total = len(self._items)
        self._progress_label.setText(f"{self._current_index + 1} / {total} 件")

        # タグバッジ
        if item.tag:
            tag_name = TAG_DISPLAY_NAMES.get(item.tag.value, item.tag.value)
            tag_color = TAG_COLORS.get(item.tag.value, COLORS["accent_blue"])
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
        else:
            self._tag_label.setText("")

        # スライダーリセット
        self._importance_slider.setValue(5)
        self._urgency_slider.setValue(5)

        # 最後のアイテムならボタンテキストを変更
        if self._current_index == len(self._items) - 1:
            self._set_btn.setText("設定して完了")
        else:
            self._set_btn.setText("設定して次へ")

    def _on_set(self) -> None:
        """設定ボタンのハンドラ."""
        item = self._items[self._current_index]
        importance = self._importance_slider.value()
        urgency = self._urgency_slider.value()

        self._logic.set_importance_urgency(item.id, importance, urgency)

        self._current_index += 1
        if self._current_index >= len(self._items):
            self.accept()
        else:
            self._show_current_item()

    def closeEvent(self, event: QCloseEvent) -> None:
        """ダイアログの閉じるイベントを無効化する."""
        event.ignore()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Escapeキーによる閉じるを無効化する."""
        if event.key() == Qt.Key.Key_Escape:
            event.ignore()
            return
        super().keyPressEvent(event)


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
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("整理 - 重要度×緊急度")
        title.setProperty("heading", True)
        layout.addWidget(title)

        desc = QLabel("タスクの重要度と緊急度をマトリクスで確認できます")
        desc.setProperty("subheading", True)
        layout.addWidget(desc)

        self._status_label = QLabel("評価するタスクはありません")
        self._status_label.setProperty("muted", True)
        layout.addWidget(self._status_label)

        # マトリクスビュー（常時表示）
        self._matrix_view = MatrixView()
        layout.addWidget(self._matrix_view, 1)

    def _update_matrix(self) -> None:
        """マトリクスビューを更新する."""
        tasks = self._repo.get_tasks()
        scored = [
            item
            for item in tasks
            if item.importance is not None and item.urgency is not None
        ]
        self._matrix_view.set_items(scored)

    def refresh(self) -> None:
        """表示を更新する."""
        self._update_matrix()

        pending = self._logic.get_unorganized_tasks()
        if pending:
            self._status_label.setText(f"未評価のタスクが {len(pending)} 件あります")
            dlg = OrganizationDialog(pending, self._logic, parent=self)
            dlg.exec()
            self.data_changed.emit()
            self._update_matrix()
            self._status_label.setText("評価するタスクはありません")
        else:
            self._status_label.setText("評価するタスクはありません")
