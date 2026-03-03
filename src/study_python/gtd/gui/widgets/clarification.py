"""明確化フェーズウィジェット.

「いつかやる」アイテムをウィザード形式で分類するUI。
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from study_python.gtd.gui.styles import (
    COLORS,
    ENERGY_DISPLAY_NAMES,
    LOCATION_DISPLAY_NAMES,
    TIME_ESTIMATE_DISPLAY_NAMES,
)
from study_python.gtd.logic.clarification import ClarificationLogic
from study_python.gtd.models import EnergyLevel, GtdItem, Location, TimeEstimate
from study_python.gtd.repository import GtdRepository


logger = logging.getLogger(__name__)


class ClarificationWidget(QWidget):
    """明確化フェーズウィジェット.

    Signals:
        data_changed: データが変更された時に発火。
    """

    data_changed = Signal()

    def __init__(
        self, repository: GtdRepository, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._repo = repository
        self._logic = ClarificationLogic(repository)
        self._current_item: GtdItem | None = None
        self._pending_items: list[GtdItem] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # タイトル
        title = QLabel("明確化")
        title.setProperty("heading", True)
        layout.addWidget(title)

        self._desc = QLabel("「いつかやる」アイテムを分類します")
        self._desc.setProperty("subheading", True)
        layout.addWidget(self._desc)

        # 進捗
        self._progress_label = QLabel("")
        self._progress_label.setProperty("muted", True)
        layout.addWidget(self._progress_label)

        # アイテム表示エリア
        self._item_display = QLabel("")
        self._item_display.setStyleSheet(
            f"""
            background-color: {COLORS["bg_secondary"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            padding: 20px;
            font-size: 18px;
            font-weight: bold;
            """
        )
        self._item_display.setWordWrap(True)
        layout.addWidget(self._item_display)

        # 質問・選択エリア
        self._question_label = QLabel("")
        self._question_label.setStyleSheet("font-size: 15px; margin-top: 8px;")
        layout.addWidget(self._question_label)

        # ボタン行
        self._btn_layout = QHBoxLayout()
        self._btn_layout.setSpacing(12)

        self._yes_btn = QPushButton("はい")
        self._yes_btn.setFixedWidth(120)
        self._yes_btn.clicked.connect(self._on_yes)
        self._btn_layout.addWidget(self._yes_btn)

        self._no_btn = QPushButton("いいえ")
        self._no_btn.setFixedWidth(120)
        self._no_btn.setProperty("secondary", True)
        self._no_btn.clicked.connect(self._on_no)
        self._btn_layout.addWidget(self._no_btn)

        self._btn_layout.addStretch()
        layout.addLayout(self._btn_layout)

        # タスクContext入力エリア（タスク分類時に表示）
        self._context_widget = QWidget()
        self._context_widget.setVisible(False)
        context_layout = QVBoxLayout(self._context_widget)
        context_layout.setSpacing(8)

        required_style = f"color: {COLORS['accent_red']}; font-weight: bold;"

        # 場所（複数選択・必須）
        loc_label = QLabel("実施場所（複数選択可）: *")
        loc_label.setStyleSheet(required_style)
        context_layout.addWidget(loc_label)
        self._location_checks: dict[str, QCheckBox] = {}
        loc_layout = QHBoxLayout()
        for loc in Location:
            cb = QCheckBox(LOCATION_DISPLAY_NAMES[loc.value])
            self._location_checks[loc.value] = cb
            loc_layout.addWidget(cb)
        loc_layout.addStretch()
        context_layout.addLayout(loc_layout)

        # 時間（必須）
        time_label = QLabel("所要時間: *")
        time_label.setStyleSheet(required_style)
        context_layout.addWidget(time_label)
        self._time_combo = QComboBox()
        for te in TimeEstimate:
            self._time_combo.addItem(TIME_ESTIMATE_DISPLAY_NAMES[te.value], te.value)
        context_layout.addWidget(self._time_combo)

        # エネルギー（必須）
        energy_label = QLabel("必要なエネルギー: *")
        energy_label.setStyleSheet(required_style)
        context_layout.addWidget(energy_label)
        self._energy_radios: dict[str, QRadioButton] = {}
        energy_layout = QHBoxLayout()
        for el in EnergyLevel:
            rb = QRadioButton(ENERGY_DISPLAY_NAMES[el.value])
            self._energy_radios[el.value] = rb
            energy_layout.addWidget(rb)
        energy_layout.addStretch()
        context_layout.addLayout(energy_layout)

        # デフォルト値を設定
        self._reset_context_defaults()

        # バリデーションエラーラベル
        self._validation_error = QLabel("")
        self._validation_error.setStyleSheet(
            f"color: {COLORS['accent_red']}; font-size: 12px;"
        )
        self._validation_error.setVisible(False)
        context_layout.addWidget(self._validation_error)

        # 必須注記
        required_note = QLabel("* は必須項目です")
        required_note.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        context_layout.addWidget(required_note)

        # 確定ボタン
        confirm_btn = QPushButton("タスクとして登録")
        confirm_btn.clicked.connect(self._on_confirm_task)
        context_layout.addWidget(confirm_btn)

        layout.addWidget(self._context_widget)

        # 完了メッセージ
        self._empty_label = QLabel("分類するアイテムはありません")
        self._empty_label.setProperty("subheading", True)
        self._empty_label.setVisible(False)
        layout.addWidget(self._empty_label)

        layout.addStretch()

        # 状態管理: 決定木のステップ
        self._step = 0  # 0: 自分でやる? 1: 日時明確? 2: 2step? 3: 数分?

    def refresh(self) -> None:
        """表示を更新する."""
        self._pending_items = self._logic.get_pending_items()
        self._step = 0
        self._context_widget.setVisible(False)

        if self._pending_items:
            self._current_item = self._pending_items[0]
            self._show_current_item()
            self._show_step()
            self._set_buttons_visible(True)
            self._empty_label.setVisible(False)
        else:
            self._current_item = None
            self._item_display.setText("")
            self._question_label.setText("")
            self._set_buttons_visible(False)
            self._empty_label.setVisible(True)
            self._progress_label.setText("")

    def _show_current_item(self) -> None:
        """現在のアイテム情報を表示する."""
        if self._current_item is None:
            return
        self._item_display.setText(self._current_item.title)
        idx = self._pending_items.index(self._current_item) + 1
        total = len(self._pending_items)
        self._progress_label.setText(f"{idx} / {total} 件")

    def _show_step(self) -> None:
        """現在のステップの質問を表示する."""
        questions = [
            "自身が実施しなくてはいけないですか？",
            "日時が明確ですか？",
            "2ステップ以上のアクションが必要ですか？",
            "数分で実施できますか？",
        ]
        if self._step < len(questions):
            self._question_label.setText(questions[self._step])

    def _set_buttons_visible(self, visible: bool) -> None:
        """Yes/Noボタンの表示を切り替える."""
        self._yes_btn.setVisible(visible)
        self._no_btn.setVisible(visible)

    def _on_yes(self) -> None:
        """「はい」ボタンのハンドラ."""
        if self._current_item is None:
            return

        item_id = self._current_item.id

        if self._step == 0:
            # 自分でやる → 次の質問へ
            self._step = 1
            self._show_step()
        elif self._step == 1:
            # 日時明確 → カレンダー
            self._logic.classify_as_calendar(item_id)
            self._advance_to_next_item()
        elif self._step == 2:
            # 2step以上 → プロジェクト
            self._logic.classify_as_project(item_id)
            self._advance_to_next_item()
        elif self._step == 3:
            # 数分で可能 → 即実行
            self._logic.classify_as_do_now(item_id)
            self._advance_to_next_item()

    def _on_no(self) -> None:
        """「いいえ」ボタンのハンドラ."""
        if self._current_item is None:
            return

        item_id = self._current_item.id

        if self._step == 0:
            # 自分でやらない → 依頼
            self._logic.classify_as_delegation(item_id)
            self._advance_to_next_item()
        elif self._step == 1:
            # 日時不明確 → 次の質問へ
            self._step = 2
            self._show_step()
        elif self._step == 2:
            # 1stepで済む → 次の質問へ
            self._step = 3
            self._show_step()
        elif self._step == 3:
            # 数分では無理 → タスク（Context入力が必要）
            self._set_buttons_visible(False)
            self._question_label.setText("タスクのContextを設定してください:")
            self._context_widget.setVisible(True)

    def _reset_context_defaults(self) -> None:
        """Context入力フォームをデフォルト値にリセットする."""
        # 場所: デスクをデフォルト選択
        for val, cb in self._location_checks.items():
            cb.setChecked(val == Location.DESK.value)

        # 時間: 30分以内をデフォルト選択
        for i in range(self._time_combo.count()):
            if self._time_combo.itemData(i) == TimeEstimate.WITHIN_30MIN.value:
                self._time_combo.setCurrentIndex(i)
                break

        # エネルギー: 中をデフォルト選択
        self._energy_radios[EnergyLevel.MEDIUM.value].setChecked(True)

    def _validate_context(self) -> str | None:
        """Context入力のバリデーションを行う.

        Returns:
            エラーメッセージ。問題なければNone。
        """
        has_location = any(cb.isChecked() for cb in self._location_checks.values())
        if not has_location:
            return "実施場所を1つ以上選択してください"

        has_energy = any(rb.isChecked() for rb in self._energy_radios.values())
        if not has_energy:
            return "必要なエネルギーを選択してください"

        return None

    def _on_confirm_task(self) -> None:
        """タスクContext確定ハンドラ."""
        if self._current_item is None:
            return

        # バリデーション
        error = self._validate_context()
        if error:
            self._validation_error.setText(error)
            self._validation_error.setVisible(True)
            return

        self._validation_error.setVisible(False)

        # 場所
        locations = [
            Location(val) for val, cb in self._location_checks.items() if cb.isChecked()
        ]

        # 時間
        time_val = self._time_combo.currentData()
        time_estimate = TimeEstimate(time_val)

        # エネルギー
        energy = EnergyLevel.MEDIUM
        for val, rb in self._energy_radios.items():
            if rb.isChecked():
                energy = EnergyLevel(val)
                break

        self._logic.classify_as_task(
            self._current_item.id,
            locations=locations,
            time_estimate=time_estimate,
            energy=energy,
        )

        self._context_widget.setVisible(False)
        # デフォルト値にリセット
        self._reset_context_defaults()

        self._advance_to_next_item()

    def _advance_to_next_item(self) -> None:
        """次のアイテムに進む."""
        self.data_changed.emit()
        self._pending_items = self._logic.get_pending_items()
        self._step = 0

        if self._pending_items:
            self._current_item = self._pending_items[0]
            self._show_current_item()
            self._show_step()
            self._set_buttons_visible(True)
        else:
            self._current_item = None
            self._item_display.setText("")
            self._question_label.setText("")
            self._set_buttons_visible(False)
            self._empty_label.setVisible(True)
            self._progress_label.setText("")
