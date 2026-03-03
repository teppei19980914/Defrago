"""見直しフェーズウィジェット.

完了タスクとプロジェクトタスクのレビューを行うUI。
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from study_python.gtd.gui.components.dialogs import (
    ConfirmDialog,
    DecomposeProjectDialog,
)
from study_python.gtd.gui.components.item_card import ItemCard
from study_python.gtd.logic.review import ReviewLogic
from study_python.gtd.models import Tag
from study_python.gtd.repository import GtdRepository


logger = logging.getLogger(__name__)


class ReviewWidget(QWidget):
    """見直しフェーズウィジェット.

    Signals:
        data_changed: データが変更された時に発火。
    """

    data_changed = Signal()

    def __init__(
        self, repository: GtdRepository, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._repo = repository
        self._logic = ReviewLogic(repository)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("見直し")
        title.setProperty("heading", True)
        layout.addWidget(title)

        desc = QLabel("完了タスクとプロジェクトを振り返り、整理しましょう")
        desc.setProperty("subheading", True)
        layout.addWidget(desc)

        self._count_label = QLabel("")
        self._count_label.setProperty("muted", True)
        layout.addWidget(self._count_label)

        # レビュー対象リスト
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        layout.addWidget(scroll, 1)

        # 空メッセージ
        self._empty_label = QLabel("見直すアイテムはありません")
        self._empty_label.setProperty("subheading", True)
        self._empty_label.setVisible(False)
        layout.addWidget(self._empty_label)

    def _on_card_action(self, item_id: str, action: str) -> None:
        """カードアクションハンドラ."""
        if action == "delete":
            dlg = ConfirmDialog(
                "削除確認",
                "このアイテムを完全に削除しますか？",
                confirm_text="削除",
                parent=self,
            )
            if dlg.exec():
                self._logic.delete_item(item_id)
                self.refresh()
                self.data_changed.emit()
        elif action == "to_inbox":
            self._logic.move_to_inbox(item_id)
            self.refresh()
            self.data_changed.emit()
        elif action == "decompose":
            item = self._repo.get(item_id)
            if item is None:
                return
            decompose_dlg = DecomposeProjectDialog(item.title, parent=self)
            if decompose_dlg.exec():
                titles = decompose_dlg.get_titles()
                if titles:
                    self._logic.decompose_project(item_id, titles)
                    self.refresh()
                    self.data_changed.emit()

    def refresh(self) -> None:
        """表示を更新する."""
        # 既存カードをクリア
        while self._list_layout.count() > 1:
            child = self._list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        items = self._logic.get_review_items()

        self._count_label.setText(
            f"完了: {self._logic.get_completed_count()} 件  "
            f"プロジェクト: {self._logic.get_project_count()} 件"
        )
        self._empty_label.setVisible(len(items) == 0)

        for item in items:
            if item.tag == Tag.PROJECT:
                actions = [
                    ("decompose", "細分化"),
                    ("delete", "削除"),
                ]
            else:
                actions = [
                    ("to_inbox", "Inboxに戻す"),
                    ("delete", "削除"),
                ]
            card = ItemCard(
                item,
                actions=actions,
                parent=self._list_container,
            )
            card.action_triggered.connect(self._on_card_action)
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)
