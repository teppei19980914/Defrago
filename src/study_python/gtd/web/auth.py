"""認証モジュール.

SHA-256ハッシュによるシンプルなパスワード検証を提供する。
"""

from __future__ import annotations

import hashlib
import hmac
import logging

from study_python.gtd.web.config import get_settings


logger = logging.getLogger(__name__)


def verify_password(plain_password: str) -> bool:
    """パスワードを検証する.

    Args:
        plain_password: 入力されたパスワード。

    Returns:
        ハッシュが一致する場合True。
    """
    settings = get_settings()
    input_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    return hmac.compare_digest(input_hash, settings.admin_password_hash)


def verify_credentials(username: str, password: str) -> bool:
    """認証情報を検証する.

    Args:
        username: ユーザー名。
        password: パスワード。

    Returns:
        認証成功の場合True。
    """
    settings = get_settings()
    if username != settings.admin_username:
        return False
    return verify_password(password)
