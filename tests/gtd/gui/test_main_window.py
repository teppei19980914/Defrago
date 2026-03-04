"""メインウィンドウのGUIテスト."""

from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from study_python.gtd.gui.main_window import MainWindow
from study_python.gtd.models import GtdItem, ItemStatus, Tag, TaskStatus
from study_python.gtd.repository import GtdRepository
from study_python.gtd.settings import SettingsManager


@pytest.fixture
def repo(tmp_path: Path) -> GtdRepository:
    return GtdRepository(data_path=tmp_path / "test.json")


@pytest.fixture
def settings_mgr(tmp_path: Path) -> SettingsManager:
    return SettingsManager(settings_path=tmp_path / "test_settings.json")


@pytest.fixture
def window(
    qtbot: QtBot, repo: GtdRepository, settings_mgr: SettingsManager
) -> MainWindow:
    w = MainWindow(repo, settings_mgr)
    qtbot.addWidget(w)
    return w


class TestMainWindow:
    """MainWindowのテスト."""

    def test_window_title(self, window: MainWindow):
        assert "MindFlow" in window.windowTitle()

    def test_initial_page_is_dashboard(self, window: MainWindow):
        assert window._stack.currentIndex() == 0

    def test_navigate_to_inbox(self, window: MainWindow):
        window._nav_buttons["inbox"].click()
        assert window._stack.currentIndex() == 1

    def test_navigate_to_clarification(self, window: MainWindow):
        window._nav_buttons["clarification"].click()
        assert window._stack.currentIndex() == 2

    def test_navigate_to_organization(self, window: MainWindow):
        window._nav_buttons["organization"].click()
        assert window._stack.currentIndex() == 3

    def test_navigate_to_execution(self, window: MainWindow):
        window._nav_buttons["execution"].click()
        assert window._stack.currentIndex() == 4

    def test_navigate_to_review(self, window: MainWindow):
        window._nav_buttons["review"].click()
        assert window._stack.currentIndex() == 5

    def test_badge_updates_on_data_change(
        self, window: MainWindow, repo: GtdRepository
    ):
        repo.add(GtdItem(title="テスト", item_status=ItemStatus.INBOX))
        window._update_badges()
        assert "(1)" in window._nav_buttons["inbox"].text()

    def test_status_bar_updates(self, window: MainWindow, repo: GtdRepository):
        repo.add(GtdItem(title="テスト", tag=Tag.TASK, status=TaskStatus.DONE.value))
        window._update_status_bar()
        assert "Done: 1" in window._status_bar.currentMessage()

    def test_data_changed_saves(self, window: MainWindow, repo: GtdRepository):
        repo.add(GtdItem(title="保存テスト"))
        window._on_data_changed()
        assert repo.data_path.exists()
