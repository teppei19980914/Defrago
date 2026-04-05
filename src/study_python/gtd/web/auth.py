"""認証モジュール.

bcryptによるパスワード検証とユーザー管理を提供する。
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import UTC, datetime

import bcrypt
from sqlalchemy.orm import Session

from study_python.gtd.web.db_models import UserRow
from study_python.gtd.web.labels import load_labels


logger = logging.getLogger(__name__)

# ユーザー名: 英数字・アンダースコア・ハイフン, 3-50文字
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")
# パスワード: 8文字以上
MIN_PASSWORD_LENGTH = 8


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


def _check_password(plain_password: str, hashed: str) -> bool:
    """パスワードをbcryptハッシュと照合する."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        logger.warning("Invalid password hash format")
        return False


def validate_username(username: str) -> str | None:
    """ユーザー名のバリデーション.

    Returns:
        エラーメッセージ。問題なければNone。
    """
    if not USERNAME_PATTERN.match(username):
        return load_labels()["auth"]["error_username_format"]
    return None


def validate_password(password: str) -> str | None:
    """パスワードのバリデーション.

    Returns:
        エラーメッセージ。問題なければNone。
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return load_labels()["auth"]["error_password_length"]
    return None


def verify_credentials(
    session: Session, username: str, password: str
) -> UserRow | None:
    """認証情報を検証する.

    Args:
        session: DBセッション。
        username: ユーザー名。
        password: パスワード。

    Returns:
        認証成功時はUserRow。失敗時はNone。
    """
    user = session.query(UserRow).filter(UserRow.username == username).first()
    if user is None:
        # タイミング攻撃を防ぐためダミーチェック
        _check_password(
            password, "$2b$12$dummy.hash.to.prevent.timing.attack.000000000000000000000"
        )
        return None
    if _check_password(password, user.password_hash):
        return user
    return None


def register_user(session: Session, username: str, password: str) -> UserRow | None:
    """新規ユーザーを登録する.

    Args:
        session: DBセッション。
        username: ユーザー名。
        password: パスワード。

    Returns:
        作成されたUserRow。ユーザー名重複時はNone。
    """
    existing = session.query(UserRow).filter(UserRow.username == username).first()
    if existing is not None:
        return None

    user = UserRow(
        id=str(uuid.uuid4()),
        username=username,
        password_hash=hash_password(password),
        created_at=datetime.now(tz=UTC).isoformat(),
    )
    session.add(user)
    session.flush()
    logger.info(f"User registered: {username} (id={user.id})")
    return user
