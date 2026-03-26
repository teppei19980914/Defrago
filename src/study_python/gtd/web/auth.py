"""認証モジュール.

bcryptによるパスワード検証を提供する。
"""

from __future__ import annotations

import logging

import bcrypt

from study_python.gtd.web.config import get_settings


logger = logging.getLogger(__name__)


def verify_password(plain_password: str) -> bool:
    """パスワードをbcryptハッシュと照合する.

    Args:
        plain_password: 入力されたパスワード。

    Returns:
        ハッシュが一致する場合True。
    """
    settings = get_settings()
    stored_hash = settings.admin_password_hash
    if not stored_hash:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), stored_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        logger.warning("Invalid password hash format")
        return False


def hash_password(plain_password: str) -> str:
    """パスワードのbcryptハッシュを生成する.

    Args:
        plain_password: ハッシュ化するパスワード。

    Returns:
        bcryptハッシュ文字列。
    """
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


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
