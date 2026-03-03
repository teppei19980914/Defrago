"""ログ設定モジュールのテスト。"""

import logging
import tempfile
from pathlib import Path

import pytest

from study_python.logging_config import LoggerMixin, get_logger, setup_logging


def _close_all_handlers() -> None:
    """すべてのハンドラを閉じてクリアする。"""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
    root_logger.setLevel(logging.WARNING)


class TestSetupLogging:
    """setup_logging関数のテスト。"""

    def teardown_method(self) -> None:
        """各テスト後にロガーをリセットする。"""
        _close_all_handlers()

    def test_setup_logging_creates_console_handler(self) -> None:
        """コンソールハンドラが作成されることを確認する。"""
        setup_logging(log_to_console=True, log_to_file=False)
        root_logger = logging.getLogger()

        assert len(root_logger.handlers) == 1
        assert isinstance(root_logger.handlers[0], logging.StreamHandler)

    def test_setup_logging_creates_file_handler(self) -> None:
        """ファイルハンドラが作成されることを確認する。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_to_console=False, log_to_file=True, log_dir=tmpdir)
            root_logger = logging.getLogger()

            assert len(root_logger.handlers) == 1
            # ファイルハンドラのログファイルが作成されているか確認
            log_files = list(Path(tmpdir).glob("app_*.log"))
            assert len(log_files) == 1

            # 一時ディレクトリを削除する前にハンドラを閉じる
            _close_all_handlers()

    def test_setup_logging_with_both_handlers(self) -> None:
        """コンソールとファイルの両方のハンドラが作成されることを確認する。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            setup_logging(log_to_console=True, log_to_file=True, log_dir=tmpdir)
            root_logger = logging.getLogger()

            assert len(root_logger.handlers) == 2

            # 一時ディレクトリを削除する前にハンドラを閉じる
            _close_all_handlers()

    def test_setup_logging_sets_log_level(self) -> None:
        """ログレベルが正しく設定されることを確認する。"""
        setup_logging(level=logging.DEBUG, log_to_console=True, log_to_file=False)
        root_logger = logging.getLogger()

        assert root_logger.level == logging.DEBUG

    def test_setup_logging_accepts_string_level(self) -> None:
        """文字列でログレベルを指定できることを確認する。"""
        setup_logging(level="DEBUG", log_to_console=True, log_to_file=False)
        root_logger = logging.getLogger()

        assert root_logger.level == logging.DEBUG

    def test_setup_logging_creates_log_directory(self) -> None:
        """ログディレクトリが自動作成されることを確認する。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "nested" / "logs"
            setup_logging(log_to_console=False, log_to_file=True, log_dir=log_dir)

            assert log_dir.exists()

            # 一時ディレクトリを削除する前にハンドラを閉じる
            _close_all_handlers()


class TestGetLogger:
    """get_logger関数のテスト。"""

    def test_get_logger_returns_logger(self) -> None:
        """ロガーが返されることを確認する。"""
        logger = get_logger("test_module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_get_logger_returns_same_logger(self) -> None:
        """同じ名前で呼び出すと同じロガーが返されることを確認する。"""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")

        assert logger1 is logger2


class TestLoggerMixin:
    """LoggerMixinクラスのテスト。"""

    def test_logger_mixin_provides_logger(self) -> None:
        """LoggerMixinがロガーを提供することを確認する。"""

        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        logger = obj.logger

        assert isinstance(logger, logging.Logger)
        assert "TestClass" in logger.name

    def test_logger_mixin_logger_name_includes_module(self) -> None:
        """ロガー名にモジュール名が含まれることを確認する。"""

        class AnotherTestClass(LoggerMixin):
            pass

        obj = AnotherTestClass()

        assert obj.logger.name == f"{__name__}.AnotherTestClass"
