"""共通ダイアログ.

確認ダイアログやアイテム登録ダイアログを提供する。
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from study_python.gtd.gui.styles import COLORS


logger = logging.getLogger(__name__)


class InboxInputDialog(QDialog):
    """Inboxアイテム登録ダイアログ.

    タイトルとメモを入力してアイテムを登録する。
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Inboxに登録")
        self.setMinimumWidth(450)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_primary']}; }}")
        self._title_value = ""
        self._note_value = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        heading = QLabel("新しいアイテムを登録")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        # タイトル
        title_label = QLabel("タイトル")
        layout.addWidget(title_label)
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("気になることを入力...")
        layout.addWidget(self._title_edit)

        # メモ
        note_label = QLabel("メモ（任意）")
        layout.addWidget(note_label)
        self._note_edit = QTextEdit()
        self._note_edit.setPlaceholderText("詳細な説明があれば入力...")
        self._note_edit.setMaximumHeight(100)
        layout.addWidget(self._note_edit)

        # ボタン
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        add_btn = QPushButton("登録")
        add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(add_btn)

        layout.addLayout(btn_layout)

        self._title_edit.setFocus()

    def _on_add(self) -> None:
        """登録ボタンのハンドラ."""
        self._title_value = self._title_edit.text().strip()
        self._note_value = self._note_edit.toPlainText().strip()
        if self._title_value:
            self.accept()

    def get_values(self) -> tuple[str, str]:
        """入力値を返す.

        Returns:
            (タイトル, メモ) のタプル。
        """
        return self._title_value, self._note_value


class ConfirmDialog(QDialog):
    """確認ダイアログ."""

    def __init__(
        self,
        title: str,
        message: str,
        confirm_text: str = "OK",
        cancel_text: str = "キャンセル",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_primary']}; }}")
        self._setup_ui(message, confirm_text, cancel_text)

    def _setup_ui(self, message: str, confirm_text: str, cancel_text: str) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton(confirm_text)
        confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)


class DecomposeProjectDialog(QDialog):
    """プロジェクト細分化ダイアログ.

    プロジェクトを複数のサブタスクに分解するためのダイアログ。
    """

    _MAX_ROWS = 20

    def __init__(self, project_title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("プロジェクトの細分化")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_primary']}; }}")
        self._row_edits: list[QLineEdit] = []
        self._row_widgets: list[QWidget] = []
        self._setup_ui(project_title)

    def _setup_ui(self, project_title: str) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        heading = QLabel("プロジェクトを細分化")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        project_label = QLabel(f"対象: {project_title}")
        project_label.setStyleSheet(
            f"""
            background-color: {COLORS["bg_secondary"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: bold;
            """
        )
        project_label.setWordWrap(True)
        layout.addWidget(project_label)

        desc = QLabel("サブタスクのタイトルを入力してください:")
        layout.addWidget(desc)

        # スクロール可能な入力行エリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setSpacing(6)
        self._rows_layout.addStretch()

        scroll.setWidget(self._rows_container)
        layout.addWidget(scroll, 1)

        # 行追加ボタン
        self._add_row_btn = QPushButton("＋ 行を追加")
        self._add_row_btn.setProperty("secondary", True)
        self._add_row_btn.clicked.connect(self._add_row)
        layout.addWidget(self._add_row_btn)

        # ボタン行
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._confirm_btn = QPushButton("細分化して登録")
        self._confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(self._confirm_btn)

        layout.addLayout(btn_layout)

        # 初期行を1つ追加
        self._add_row()

    def _add_row(self) -> None:
        """入力行を追加する."""
        if len(self._row_edits) >= self._MAX_ROWS:
            return

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        edit = QLineEdit()
        edit.setPlaceholderText(f"サブタスク {len(self._row_edits) + 1}")
        row_layout.addWidget(edit, 1)

        remove_btn = QPushButton("×")
        remove_btn.setFixedWidth(30)
        remove_btn.setProperty("danger", True)
        remove_btn.clicked.connect(lambda: self._remove_row(row_widget, edit))
        row_layout.addWidget(remove_btn)

        self._row_edits.append(edit)
        self._row_widgets.append(row_widget)
        self._rows_layout.insertWidget(self._rows_layout.count() - 1, row_widget)

        self._update_add_button()
        edit.setFocus()

    def _remove_row(self, row_widget: QWidget, edit: QLineEdit) -> None:
        """入力行を削除する."""
        if len(self._row_edits) <= 1:
            return
        self._row_edits.remove(edit)
        self._row_widgets.remove(row_widget)
        row_widget.deleteLater()
        self._update_add_button()

    def _update_add_button(self) -> None:
        """行追加ボタンの有効/無効を更新する."""
        self._add_row_btn.setEnabled(len(self._row_edits) < self._MAX_ROWS)

    def _on_confirm(self) -> None:
        """確定ボタンのハンドラ."""
        titles = self.get_titles()
        if titles:
            self.accept()

    def get_titles(self) -> list[str]:
        """入力されたサブタスクタイトルを返す.

        空行は除外される。

        Returns:
            サブタスクタイトルのリスト。
        """
        return [e.text().strip() for e in self._row_edits if e.text().strip()]
