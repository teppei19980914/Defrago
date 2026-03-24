"""Web設定.

環境変数から設定を読み込む。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class WebSettings:
    """Webアプリケーション設定."""

    secret_key: str = "dev-secret-change-me"
    admin_username: str = "admin"
    admin_password_hash: str = ""
    database_url: str = "sqlite:///./mindflow.db"
    debug: bool = False


@lru_cache
def get_settings() -> WebSettings:
    """環境変数から設定を読み込む.

    Returns:
        Webアプリケーション設定。
    """
    return WebSettings(
        secret_key=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        admin_username=os.environ.get("ADMIN_USERNAME", "admin"),
        admin_password_hash=os.environ.get("ADMIN_PASSWORD_HASH", ""),
        database_url=os.environ.get("DATABASE_URL", "sqlite:///./mindflow.db"),
        debug=os.environ.get("DEBUG", "false").lower() == "true",
    )
