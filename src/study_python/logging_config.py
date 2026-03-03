"""ログ設定モジュール。

プロジェクト共通のログ設定を提供する。
ログはコンソールとファイルの両方に出力され、
ファイルは logs/ ディレクトリに日付ローテーションで保存される。
"""

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Literal

# ログディレクトリ
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"

# デフォルト設定
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)-8s | "
    "%(name)s:%(funcName)s:%(lineno)d | %(message)s"
)
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_BACKUP_COUNT = 30  # 30日分保持


def setup_logging(
    level: int | str = DEFAULT_LOG_LEVEL,
    log_dir: Path | str | None = None,
    log_to_console: bool = True,
    log_to_file: bool = True,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
) -> None:
    """ログ設定を初期化する。

    Args:
        level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        log_dir: ログファイルの保存ディレクトリ（Noneの場合はデフォルト）
        log_to_console: コンソールへの出力を有効にするか
        log_to_file: ファイルへの出力を有効にするか
        log_format: ログフォーマット文字列
        date_format: 日時フォーマット文字列
    """
    # ログレベルの変換
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    # ログディレクトリの設定
    if log_dir is None:
        log_dir = LOG_DIR
    else:
        log_dir = Path(log_dir)

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 既存のハンドラをクリア
    root_logger.handlers.clear()

    # フォーマッタの作成
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # コンソールハンドラの設定
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # ファイルハンドラの設定
    if log_to_file:
        # ログディレクトリの作成
        log_dir.mkdir(parents=True, exist_ok=True)

        # 日付ベースのログファイル名
        log_file = log_dir / f"app_{datetime.now().strftime('%Y-%m-%d')}.log"

        # ローテーティングファイルハンドラ
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=DEFAULT_MAX_BYTES,
            backupCount=DEFAULT_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """指定された名前のロガーを取得する。

    Args:
        name: ロガー名（通常は __name__ を使用）

    Returns:
        設定済みのロガーインスタンス
    """
    return logging.getLogger(name)


class LoggerMixin:
    """ログ機能を提供するMixinクラス。

    クラスに継承させることで、self.logger でロガーにアクセスできる。

    Example:
        class MyClass(LoggerMixin):
            def do_something(self):
                self.logger.info("Doing something")
    """

    @property
    def logger(self) -> logging.Logger:
        """クラス名をベースにしたロガーを返す。"""
        return logging.getLogger(self.__class__.__module__ + "." + self.__class__.__name__)
