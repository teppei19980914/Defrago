"""QSSスタイル定義.

アプリケーション全体のスタイルシートを提供する。
"""

# カラーパレット
COLORS = {
    "bg_primary": "#1e1e2e",
    "bg_secondary": "#313244",
    "bg_surface": "#45475a",
    "bg_hover": "#585b70",
    "text_primary": "#cdd6f4",
    "text_secondary": "#a6adc8",
    "text_muted": "#6c7086",
    "accent_blue": "#89b4fa",
    "accent_green": "#a6e3a1",
    "accent_red": "#f38ba8",
    "accent_yellow": "#f9e2af",
    "accent_mauve": "#cba6f7",
    "accent_peach": "#fab387",
    "accent_teal": "#94e2d5",
    "border": "#585b70",
    "q1_color": "#f38ba8",  # 緊急×重要（赤）
    "q2_color": "#89b4fa",  # 重要（青）
    "q3_color": "#fab387",  # 緊急（オレンジ）
    "q4_color": "#6c7086",  # どちらでもない（灰）
}

MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS["bg_primary"]};
}}

QWidget {{
    color: {COLORS["text_primary"]};
    font-family: "Segoe UI", "Yu Gothic UI", "Meiryo UI", sans-serif;
    font-size: 13px;
}}

/* サイドバー */
#sidebar {{
    background-color: {COLORS["bg_secondary"]};
    border-right: 1px solid {COLORS["border"]};
}}

#sidebar QPushButton {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    color: {COLORS["text_secondary"]};
    font-size: 13px;
}}

#sidebar QPushButton:hover {{
    background-color: {COLORS["bg_surface"]};
    color: {COLORS["text_primary"]};
}}

#sidebar QPushButton:checked {{
    background-color: {COLORS["accent_blue"]};
    color: {COLORS["bg_primary"]};
    font-weight: bold;
}}

/* コンテンツエリア */
#content_area {{
    background-color: {COLORS["bg_primary"]};
}}

/* カード */
.item-card {{
    background-color: {COLORS["bg_secondary"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    padding: 12px;
}}

/* 入力フィールド */
QLineEdit {{
    background-color: {COLORS["bg_surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 12px;
    color: {COLORS["text_primary"]};
    font-size: 14px;
}}

QLineEdit:focus {{
    border-color: {COLORS["accent_blue"]};
}}

QLineEdit::placeholder {{
    color: {COLORS["text_muted"]};
}}

/* テキストエリア */
QTextEdit, QPlainTextEdit {{
    background-color: {COLORS["bg_surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px;
    color: {COLORS["text_primary"]};
}}

/* ボタン */
QPushButton {{
    background-color: {COLORS["accent_blue"]};
    color: {COLORS["bg_primary"]};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: #7aa8f0;
}}

QPushButton:pressed {{
    background-color: #6a98e0;
}}

QPushButton:disabled {{
    background-color: {COLORS["bg_surface"]};
    color: {COLORS["text_muted"]};
}}

/* 危険ボタン */
QPushButton[danger="true"] {{
    background-color: {COLORS["accent_red"]};
}}

QPushButton[danger="true"]:hover {{
    background-color: #e07a96;
}}

/* セカンダリボタン */
QPushButton[secondary="true"] {{
    background-color: {COLORS["bg_surface"]};
    color: {COLORS["text_primary"]};
}}

QPushButton[secondary="true"]:hover {{
    background-color: {COLORS["bg_hover"]};
}}

/* コンボボックス */
QComboBox {{
    background-color: {COLORS["bg_surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 6px 12px;
    color: {COLORS["text_primary"]};
    min-width: 120px;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_secondary"]};
    border: 1px solid {COLORS["border"]};
    color: {COLORS["text_primary"]};
    selection-background-color: {COLORS["accent_blue"]};
    selection-color: {COLORS["bg_primary"]};
}}

/* スライダー */
QSlider::groove:horizontal {{
    border: none;
    height: 6px;
    background: {COLORS["bg_surface"]};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: {COLORS["accent_blue"]};
    border: none;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}}

QSlider::sub-page:horizontal {{
    background: {COLORS["accent_blue"]};
    border-radius: 3px;
}}

/* チェックボックス */
QCheckBox {{
    spacing: 8px;
    color: {COLORS["text_primary"]};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS["border"]};
    border-radius: 4px;
    background-color: {COLORS["bg_surface"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["accent_blue"]};
    border-color: {COLORS["accent_blue"]};
}}

/* ラジオボタン */
QRadioButton {{
    spacing: 8px;
    color: {COLORS["text_primary"]};
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {COLORS["border"]};
    border-radius: 9px;
    background-color: {COLORS["bg_surface"]};
}}

QRadioButton::indicator:checked {{
    background-color: {COLORS["accent_blue"]};
    border-color: {COLORS["accent_blue"]};
}}

/* ラベル */
QLabel {{
    color: {COLORS["text_primary"]};
}}

QLabel[heading="true"] {{
    font-size: 20px;
    font-weight: bold;
    color: {COLORS["text_primary"]};
}}

QLabel[subheading="true"] {{
    font-size: 14px;
    color: {COLORS["text_secondary"]};
}}

QLabel[muted="true"] {{
    color: {COLORS["text_muted"]};
    font-size: 12px;
}}

/* スクロールエリア */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollArea > QWidget > QWidget {{
    background-color: transparent;
}}

QScrollBar:vertical {{
    background: {COLORS["bg_primary"]};
    width: 8px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["bg_surface"]};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["bg_hover"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* ステータスバー */
QStatusBar {{
    background-color: {COLORS["bg_secondary"]};
    color: {COLORS["text_secondary"]};
    border-top: 1px solid {COLORS["border"]};
    font-size: 12px;
}}

/* セパレータ */
QFrame[frameShape="4"] {{
    color: {COLORS["border"]};
    max-height: 1px;
}}

/* グループボックス */
QGroupBox {{
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    color: {COLORS["text_primary"]};
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}}
"""

# タグごとの色定義
TAG_COLORS = {
    "delegation": COLORS["accent_mauve"],
    "calendar": COLORS["accent_teal"],
    "project": COLORS["accent_yellow"],
    "do_now": COLORS["accent_red"],
    "task": COLORS["accent_blue"],
}

# 日本語表示名
TAG_DISPLAY_NAMES = {
    "delegation": "依頼",
    "calendar": "カレンダー",
    "project": "プロジェクト",
    "do_now": "即実行",
    "task": "タスク",
}

STATUS_DISPLAY_NAMES = {
    "not_started": "未着手",
    "waiting": "連絡待ち",
    "registered": "カレンダー登録済み",
    "in_progress": "実施中",
    "done": "完了",
}

LOCATION_DISPLAY_NAMES = {
    "desk": "デスク",
    "home": "自宅",
    "commute": "移動中",
}

TIME_ESTIMATE_DISPLAY_NAMES = {
    "10min": "10分以内",
    "30min": "30分以内",
    "1hour": "1時間以内",
}

ENERGY_DISPLAY_NAMES = {
    "low": "低",
    "medium": "中",
    "high": "高",
}
