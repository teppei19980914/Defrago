"""収集フェーズウィジェット.

Inboxへのアイテム登録と分類を行うUI。
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from study_python.gtd.gui.components.dialogs import ConfirmDialog
from study_python.gtd.gui.components.item_card import ItemCard
from study_python.gtd.logic.collection import CollectionLogic
from study_python.gtd.repository import GtdRepository


logger = logging.getLogger(__name__)


class InboxWidget(QWidget):
    """収集フェーズウィジェット.

    Signals:
        data_changed: データが変更された時に発火。
    """

    data_changed = Signal()

    def __init__(
        self, repository: GtdRepository, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._repo = repository
        self._logic = CollectionLogic(repository)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # タイトル
        title = QLabel("収集 - Inbox")
        title.setProperty("heading", True)
        layout.addWidget(title)

        desc = QLabel("気になることをすべて書き出しましょう")
        desc.setProperty("subheading", True)
        layout.addWidget(desc)

        # 入力エリア
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self._input = QLineEdit()
        self._input.setPlaceholderText("気になることを入力して Enter...")
        self._input.returnPressed.connect(self._on_add_item)
        input_layout.addWidget(self._input)

        add_btn = QPushButton("追加")
        add_btn.setFixedWidth(80)
        add_btn.clicked.connect(self._on_add_item)
        input_layout.addWidget(add_btn)

        layout.addLayout(input_layout)

        # アイテムリスト（スクロール可能）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        layout.addWidget(scroll, 1)

    def _on_add_item(self) -> None:
        """アイテム追加ハンドラ."""
        title = self._input.text().strip()
        if not title:
            return

        try:
            self._logic.add_to_inbox(title)
            self._input.clear()
            self._input.setFocus()
            self.refresh()
            self.data_changed.emit()
        except ValueError as e:
            logger.warning(f"Invalid input: {e}")

    def _on_card_action(self, item_id: str, action: str) -> None:
        """カードアクションハンドラ."""
        if action == "delete":
            dlg = ConfirmDialog(
                "削除確認",
                "このアイテムを削除しますか？",
                confirm_text="削除",
                parent=self,
            )
            if dlg.exec():
                self._logic.delete_item(item_id)
                self.refresh()
                self.data_changed.emit()
        elif action == "reference":
            self._logic.move_to_reference(item_id)
            self.refresh()
            self.data_changed.emit()
        elif action == "someday":
            self._logic.move_to_someday(item_id)
            self.refresh()
            self.data_changed.emit()

    def refresh(self) -> None:
        """表示を更新する."""
        # 既存カードをクリア
        while self._list_layout.count() > 1:
            child = self._list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Inboxアイテムを表示
        items = self._logic.get_inbox_items()
        for item in items:
            card = ItemCard(
                item,
                actions=[
                    ("someday", "いつかやる"),
                    ("reference", "参考資料"),
                    ("delete", "削除"),
                ],
                parent=self._list_container,
            )
            card.action_triggered.connect(self._on_card_action)
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)
