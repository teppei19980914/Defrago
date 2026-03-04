"""GTDアプリケーションのエントリポイント."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from study_python.gtd.gui.main_window import MainWindow
from study_python.gtd.repository import GtdRepository
from study_python.gtd.settings import SettingsManager
from study_python.logging_config import setup_logging


logger = logging.getLogger(__name__)


def main() -> None:
    """アプリケーションを起動する."""
    setup_logging(level="INFO", log_to_file=True, log_to_console=True)
    logger.info("MindFlow starting...")

    repo = GtdRepository()
    repo.load()
    logger.info(f"Loaded {len(repo.items)} items")

    settings_mgr = SettingsManager()
    settings_mgr.load()
    logger.info("Settings loaded")

    app = QApplication(sys.argv)
    window = MainWindow(repo, settings_mgr)
    window.show()

    logger.info("MindFlow GUI ready")
    sys.exit(app.exec())


if __name__ == "__main__":  # pragma: no cover
    main()
