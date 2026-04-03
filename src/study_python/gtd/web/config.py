"""Web設定.

環境変数から設定を読み込む。
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebSettings:
    """Webアプリケーション設定."""

    secret_key: str = ""
    database_url: str = "sqlite:///./mindflow.db"
    debug: bool = False


@lru_cache
def get_settings() -> WebSettings:
    """環境変数から設定を読み込む.

    Returns:
        Webアプリケーション設定。

    Raises:
        ValueError: 必須の環境変数が未設定の場合。
    """
    secret_key = os.environ.get("SECRET_KEY", "")
    if not secret_key:
        msg = "SECRET_KEY environment variable must be set"
        raise ValueError(msg)

    return WebSettings(
        secret_key=secret_key,
        database_url=os.environ.get("DATABASE_URL", "sqlite:///./mindflow.db"),
        debug=os.environ.get("DEBUG", "false").lower() == "true",
    )
