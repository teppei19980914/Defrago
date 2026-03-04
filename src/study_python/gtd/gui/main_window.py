"""メインウィンドウ.

サイドバーナビゲーションとコンテンツエリアを管理する。
"""

from __future__ import annotations

import logging

from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from study_python.gtd.gui.components.dialogs import SettingsDialog
from study_python.gtd.gui.styles import COLORS, MAIN_STYLESHEET
from study_python.gtd.gui.widgets.clarification import ClarificationWidget
from study_python.gtd.gui.widgets.dashboard import DashboardWidget
from study_python.gtd.gui.widgets.inbox import InboxWidget
from study_python.gtd.gui.widgets.organization import OrganizationWidget
from study_python.gtd.gui.widgets.review import ReviewWidget
from study_python.gtd.gui.widgets.task_list import TaskListWidget
from study_python.gtd.models import ItemStatus
from study_python.gtd.repository import GtdRepository
from study_python.gtd.settings import SettingsManager


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """MindFlowメインウィンドウ."""

    def __init__(
        self, repository: GtdRepository, settings_mgr: SettingsManager
    ) -> None:
        super().__init__()
        self._repo = repository
        self._settings_mgr = settings_mgr
        self.setWindowTitle("MindFlow - GTD Task Manager")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(MAIN_STYLESHEET)

        self._setup_ui()
        self._refresh_all()

    def _setup_ui(self) -> None:
        """UIを構築する."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # サイドバー
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(4)
        sidebar_layout.setContentsMargins(8, 16, 8, 16)

        # アプリタイトル
        app_title = QLabel("MindFlow")
        app_title.setStyleSheet(
            f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS["accent_blue"]};
            padding: 8px 16px 16px 16px;
            """
        )
        sidebar_layout.addWidget(app_title)

        # ナビゲーションボタン
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)

        nav_items = [
            ("dashboard", "Dashboard"),
            ("inbox", "Inbox"),
            ("clarification", "明確化"),
            ("organization", "整理"),
            ("execution", "実行"),
            ("review", "見直し"),
        ]

        self._nav_buttons: dict[str, QPushButton] = {}
        self._badge_labels: dict[str, str] = {}

        for key, label in nav_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setObjectName(f"nav_{key}")
            self._nav_group.addButton(btn)
            self._nav_buttons[key] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # 設定ボタン（サイドバー下部）
        self._settings_btn = QPushButton("⚙ 設定")
        self._settings_btn.setObjectName("settings_btn")
        self._settings_btn.clicked.connect(self._on_settings)
        sidebar_layout.addWidget(self._settings_btn)

        main_layout.addWidget(sidebar)

        # コンテンツエリア（スタック）
        self._stack = QStackedWidget()
        self._stack.setObjectName("content_area")

        # ウィジェット生成
        self._dashboard = DashboardWidget(self._repo)
        self._inbox = InboxWidget(self._repo)
        self._clarification = ClarificationWidget(self._repo)
        self._organization = OrganizationWidget(self._repo)
        self._task_list = TaskListWidget(self._repo, self._settings_mgr)
        self._review = ReviewWidget(self._repo)

        self._stack.addWidget(self._dashboard)
        self._stack.addWidget(self._inbox)
        self._stack.addWidget(self._clarification)
        self._stack.addWidget(self._organization)
        self._stack.addWidget(self._task_list)
        self._stack.addWidget(self._review)

        main_layout.addWidget(self._stack, 1)

        # シグナル接続
        self._nav_buttons["dashboard"].clicked.connect(lambda: self._switch_page(0))
        self._nav_buttons["inbox"].clicked.connect(lambda: self._switch_page(1))
        self._nav_buttons["clarification"].clicked.connect(lambda: self._switch_page(2))
        self._nav_buttons["organization"].clicked.connect(lambda: self._switch_page(3))
        self._nav_buttons["execution"].clicked.connect(lambda: self._switch_page(4))
        self._nav_buttons["review"].clicked.connect(lambda: self._switch_page(5))

        # データ変更シグナル
        self._inbox.data_changed.connect(self._on_data_changed)
        self._clarification.data_changed.connect(self._on_data_changed)
        self._organization.data_changed.connect(self._on_data_changed)
        self._task_list.data_changed.connect(self._on_data_changed)
        self._review.data_changed.connect(self._on_data_changed)

        # 初期選択
        self._nav_buttons["dashboard"].setChecked(True)
        self._stack.setCurrentIndex(0)

        # ステータスバー
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

    def _switch_page(self, index: int) -> None:
        """ページを切り替える.

        Args:
            index: ページインデックス。
        """
        self._stack.setCurrentIndex(index)
        self._refresh_current_page()

    def _refresh_current_page(self) -> None:
        """現在のページを更新する."""
        current = self._stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()

    def _on_data_changed(self) -> None:
        """データ変更時のハンドラ."""
        self._repo.save()
        self._update_badges()
        self._update_status_bar()

    def _refresh_all(self) -> None:
        """全ページを更新する."""
        self._dashboard.refresh()
        self._inbox.refresh()
        self._clarification.refresh()
        self._organization.refresh()
        self._task_list.refresh()
        self._review.refresh()
        self._update_badges()
        self._update_status_bar()

    def _update_badges(self) -> None:
        """サイドバーのバッジ数を更新する."""
        inbox_count = len(self._repo.get_by_status(ItemStatus.INBOX))
        someday_count = len(
            [
                item
                for item in self._repo.get_by_status(ItemStatus.SOMEDAY)
                if item.tag is None
            ]
        )
        unorg_count = sum(
            1 for item in self._repo.get_tasks() if item.needs_organization()
        )
        active_count = sum(
            1
            for item in self._repo.get_tasks()
            if not item.is_done() and item.tag is not None
        )
        review_count = sum(1 for item in self._repo.get_tasks() if item.needs_review())

        self._nav_buttons["inbox"].setText(
            f"Inbox ({inbox_count})" if inbox_count else "Inbox"
        )
        self._nav_buttons["clarification"].setText(
            f"明確化 ({someday_count})" if someday_count else "明確化"
        )
        self._nav_buttons["organization"].setText(
            f"整理 ({unorg_count})" if unorg_count else "整理"
        )
        self._nav_buttons["execution"].setText(
            f"実行 ({active_count})" if active_count else "実行"
        )
        self._nav_buttons["review"].setText(
            f"見直し ({review_count})" if review_count else "見直し"
        )

    def _update_status_bar(self) -> None:
        """ステータスバーを更新する."""
        total = len(self._repo.items)
        tasks = len(self._repo.get_tasks())
        done = sum(1 for item in self._repo.get_tasks() if item.is_done())
        self._status_bar.showMessage(
            f"  Total: {total}  |  Tasks: {tasks}  |  Done: {done}"
        )

    def _on_settings(self) -> None:
        """設定ボタンのハンドラ."""
        dlg = SettingsDialog(self._repo.data_path, self._settings_mgr, parent=self)
        if dlg.exec():
            self._refresh_current_page()
