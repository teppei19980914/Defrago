"""ラベル管理モジュール.

ユーザー向けテキストをlabels.jsonから読み込む。
ハードコーディング禁止ルールに基づき、全テキストはこのモジュール経由で取得する。
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


STATIC_DIR = Path(__file__).parent / "static"


@lru_cache(maxsize=1)
def load_labels() -> dict:
    """labels.jsonからラベルを読み込む.

    Returns:
        ラベル辞書。ネストされたキーでアクセス可能。
    """
    path = STATIC_DIR / "labels.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def get_label(key: str, default: str = "") -> str:
    """ドット区切りキーでラベルを取得する.

    Args:
        key: ドット区切りキー（例: "auth.login"）。
        default: 見つからない場合のデフォルト値。

    Returns:
        ラベル文字列。
    """
    labels = load_labels()
    parts = key.split(".")
    current: dict | str = labels
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part, default)
        else:
            return default
    return str(current) if current != default else default
