"""共通ダイアログ.

確認ダイアログやアイテム登録ダイアログを提供する。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
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
from study_python.gtd.settings import (
    SettingsManager,
    SortCriterion,
    SortDirection,
    SortField,
)


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
        self._add_row_btn.setAutoDefault(False)
        self._add_row_btn.setProperty("secondary", True)
        self._add_row_btn.clicked.connect(self._add_row)
        layout.addWidget(self._add_row_btn)

        # ボタン行
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setAutoDefault(False)
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self._confirm_btn = QPushButton("細分化して登録")
        self._confirm_btn.setAutoDefault(False)
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
        edit.setPlaceholderText(
            f"サブタスク {len(self._row_edits) + 1} を入力して Enter で次の行を追加..."
        )
        edit.returnPressed.connect(self._add_row)
        row_layout.addWidget(edit, 1)

        remove_btn = QPushButton("× 削除")
        remove_btn.setFixedWidth(70)
        remove_btn.setAutoDefault(False)
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


class SettingsDialog(QDialog):
    """設定ダイアログ.

    アプリケーション情報、ソート設定、表示設定を管理する。
    """

    _SORT_FIELD_NAMES: ClassVar[dict[str, str]] = {
        SortField.TAG.value: "タグ",
        SortField.IMPORTANCE.value: "重要度",
        SortField.URGENCY.value: "緊急度",
        SortField.STATUS.value: "状況",
    }

    _SORT_DIRECTION_NAMES: ClassVar[dict[str, str]] = {
        SortDirection.ASCENDING.value: "昇順",
        SortDirection.DESCENDING.value: "降順",
    }

    _MAX_CRITERIA = 4

    def __init__(
        self,
        data_file_path: Path,
        settings_mgr: SettingsManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings_mgr = settings_mgr
        self._criteria_rows: list[_CriterionRow] = []
        self.setWindowTitle("設定")
        self.setMinimumWidth(500)
        self.setMinimumHeight(550)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_primary']}; }}")
        self._setup_ui(data_file_path)

    def _setup_ui(self, data_file_path: Path) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        heading = QLabel("⚙ 設定")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        # スクロールエリア
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)

        # --- アプリケーション情報 ---
        app_heading = QLabel("アプリケーション情報")
        app_heading.setStyleSheet("font-weight: bold; font-size: 14px;")
        scroll_layout.addWidget(app_heading)

        info_items = [
            ("アプリケーション名", "MindFlow"),
            ("バージョン", "1.0.0"),
            ("フレームワーク", "PySide6 (Qt)"),
        ]
        for label_text, value_text in info_items:
            row = QHBoxLayout()
            label = QLabel(f"{label_text}:")
            label.setProperty("muted", True)
            label.setFixedWidth(140)
            row.addWidget(label)
            value = QLabel(value_text)
            row.addWidget(value)
            row.addStretch()
            scroll_layout.addLayout(row)

        # セパレータ
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        scroll_layout.addWidget(sep1)

        # --- データ保存先 ---
        data_heading = QLabel("データ保存先")
        data_heading.setStyleSheet("font-weight: bold; font-size: 14px;")
        scroll_layout.addWidget(data_heading)

        path_label = QLabel(str(data_file_path))
        path_label.setWordWrap(True)
        path_label.setStyleSheet(
            f"""
            background-color: {COLORS["bg_secondary"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            """
        )
        path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        scroll_layout.addWidget(path_label)

        # セパレータ
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        scroll_layout.addWidget(sep2)

        # --- ソート設定 ---
        sort_heading = QLabel("ソート設定")
        sort_heading.setStyleSheet("font-weight: bold; font-size: 14px;")
        scroll_layout.addWidget(sort_heading)

        sort_desc = QLabel("タスク一覧のソート順を設定します。上の条件が優先されます。")
        sort_desc.setProperty("muted", True)
        scroll_layout.addWidget(sort_desc)

        self._criteria_container = QWidget()
        self._criteria_layout = QVBoxLayout(self._criteria_container)
        self._criteria_layout.setSpacing(6)
        self._criteria_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addWidget(self._criteria_container)

        self._add_criterion_btn = QPushButton("＋ 条件を追加")
        self._add_criterion_btn.setProperty("secondary", True)
        self._add_criterion_btn.clicked.connect(
            lambda _checked: self._add_criterion_row()
        )
        scroll_layout.addWidget(self._add_criterion_btn)

        # セパレータ
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        scroll_layout.addWidget(sep3)

        # --- 表示設定 ---
        display_heading = QLabel("表示設定")
        display_heading.setStyleSheet("font-weight: bold; font-size: 14px;")
        scroll_layout.addWidget(display_heading)

        self._show_done_cb = QCheckBox("完了タスクをタスク一覧に表示する")
        self._show_done_cb.setChecked(self._settings_mgr.settings.show_done_tasks)
        scroll_layout.addWidget(self._show_done_cb)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll, 1)

        # ボタン行
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

        # 初期条件を復元
        for criterion in self._settings_mgr.settings.sort_criteria:
            self._add_criterion_row(criterion)

    def _add_criterion_row(self, criterion: SortCriterion | None = None) -> None:
        """ソート条件行を追加する."""
        if len(self._criteria_rows) >= self._MAX_CRITERIA:
            return

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)

        num_label = QLabel(f"{len(self._criteria_rows) + 1}.")
        num_label.setFixedWidth(20)
        row_layout.addWidget(num_label)

        field_combo = QComboBox()
        for f in SortField:
            field_combo.addItem(self._SORT_FIELD_NAMES[f.value], f.value)
        if criterion:
            idx = list(SortField).index(criterion.field)
            field_combo.setCurrentIndex(idx)
        row_layout.addWidget(field_combo, 1)

        dir_combo = QComboBox()
        for d in SortDirection:
            dir_combo.addItem(self._SORT_DIRECTION_NAMES[d.value], d.value)
        if criterion:
            idx = list(SortDirection).index(criterion.direction)
            dir_combo.setCurrentIndex(idx)
        row_layout.addWidget(dir_combo)

        up_btn = QPushButton("▲")
        up_btn.setFixedSize(36, 36)
        up_btn.setProperty("secondary", True)
        up_btn.clicked.connect(lambda: self._move_criterion(row_widget, -1))
        row_layout.addWidget(up_btn)

        down_btn = QPushButton("▼")
        down_btn.setFixedSize(36, 36)
        down_btn.setProperty("secondary", True)
        down_btn.clicked.connect(lambda: self._move_criterion(row_widget, 1))
        row_layout.addWidget(down_btn)

        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(36, 36)
        remove_btn.setProperty("danger", True)
        remove_btn.clicked.connect(lambda: self._remove_criterion_row(row_widget))
        row_layout.addWidget(remove_btn)

        row = _CriterionRow(
            widget=row_widget,
            field_combo=field_combo,
            dir_combo=dir_combo,
            num_label=num_label,
        )
        self._criteria_rows.append(row)
        self._criteria_layout.addWidget(row_widget)
        self._update_criterion_buttons()

    def _remove_criterion_row(self, row_widget: QWidget) -> None:
        """ソート条件行を削除する."""
        if len(self._criteria_rows) <= 1:
            return
        for i, row in enumerate(self._criteria_rows):
            if row.widget is row_widget:
                self._criteria_rows.pop(i)
                row_widget.deleteLater()
                break
        self._update_row_numbers()
        self._update_criterion_buttons()

    def _move_criterion(self, row_widget: QWidget, direction: int) -> None:
        """条件を上下に移動する.

        Args:
            row_widget: 移動対象の行ウィジェット。
            direction: -1で上、+1で下。
        """
        for i, row in enumerate(self._criteria_rows):
            if row.widget is row_widget:
                new_idx = i + direction
                if 0 <= new_idx < len(self._criteria_rows):
                    self._criteria_rows[i], self._criteria_rows[new_idx] = (
                        self._criteria_rows[new_idx],
                        self._criteria_rows[i],
                    )
                    self._rebuild_criteria_layout()
                break

    def _rebuild_criteria_layout(self) -> None:
        """条件レイアウトを再構築する."""
        while self._criteria_layout.count():
            self._criteria_layout.takeAt(0)
        for row in self._criteria_rows:
            self._criteria_layout.addWidget(row.widget)
        self._update_row_numbers()

    def _update_row_numbers(self) -> None:
        """行番号ラベルを更新する."""
        for i, row in enumerate(self._criteria_rows):
            row.num_label.setText(f"{i + 1}.")

    def _update_criterion_buttons(self) -> None:
        """追加ボタンの有効/無効を更新する."""
        self._add_criterion_btn.setEnabled(
            len(self._criteria_rows) < self._MAX_CRITERIA
        )

    def _collect_criteria(self) -> list[SortCriterion]:
        """UIからソート条件を収集する."""
        criteria: list[SortCriterion] = []
        for row in self._criteria_rows:
            field_val = row.field_combo.currentData()
            dir_val = row.dir_combo.currentData()
            criteria.append(
                SortCriterion(
                    field=SortField(str(field_val)),
                    direction=SortDirection(str(dir_val)),
                )
            )
        return criteria

    def _on_save(self) -> None:
        """保存ボタンのハンドラ."""
        try:
            criteria = self._collect_criteria()
            self._settings_mgr.update_sort_criteria(criteria)
            self._settings_mgr.update_show_done_tasks(self._show_done_cb.isChecked())
            self._settings_mgr.save()
            self.accept()
        except ValueError as e:
            logger.warning(f"Settings validation failed: {e}")


class _CriterionRow:
    """ソート条件行の内部データ."""

    __slots__ = ("dir_combo", "field_combo", "num_label", "widget")

    def __init__(
        self,
        widget: QWidget,
        field_combo: QComboBox,
        dir_combo: QComboBox,
        num_label: QLabel,
    ) -> None:
        self.widget = widget
        self.field_combo = field_combo
        self.dir_combo = dir_combo
        self.num_label = num_label
