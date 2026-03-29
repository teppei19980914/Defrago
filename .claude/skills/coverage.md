---
name: coverage
description: テストカバレッジ方針。カバレッジ100%目標、除外ルール、pyproject.toml設定例を含む。
---

# カバレッジ方針

コードの品質を保証するため、テストカバレッジ率100%を目指す。

## 目標

- **カバレッジ率**: 100%（除外対象を除く）
- **必須**: 新規コードには必ずテストを作成する
- **CI/CD**: カバレッジが基準を下回る場合はマージをブロック

## カバレッジ実行コマンド

```bash
# カバレッジ付きテスト実行
uv run pytest --cov=src/study_python --cov-report=html --cov-report=term-missing

# カバレッジレポートの確認
# htmlcov/index.html をブラウザで開く
```

## カバレッジ除外の方法

通常の処理では到達しないコードは `# pragma: no cover` コメントで除外する。

```python
def process_data(data: dict) -> str:
    if not data:
        raise ValueError("Data cannot be empty")  # テストで検証

    try:
        result = transform(data)
        return result
    except TransformError as e:
        logger.error(f"Transform failed: {e}")
        raise
    except Exception as e:  # pragma: no cover
        # 予期しないエラー（通常到達しない）
        logger.critical(f"Unexpected error: {e}")
        raise
```

## 除外してよいケース

以下のケースのみ `# pragma: no cover` の使用を許可する：

| ケース | 理由 | 例 |
|--------|------|-----|
| 予期しない例外ハンドラ | 防御的コードで通常到達しない | `except Exception:` |
| デバッグ専用コード | 本番では実行されない | `if DEBUG:` ブロック |
| 抽象メソッド | 実装クラスでテストする | `raise NotImplementedError` |
| 型チェック専用ブロック | 実行時には不要 | `if TYPE_CHECKING:` |
| プラットフォーム固有コード | 実行環境で到達不可 | `if sys.platform == 'win32':` |
| main実行ブロック | モジュールとして使用時は不要 | `if __name__ == '__main__':` |

## 除外してはいけないケース

以下は必ずテストでカバーすること：

- **バリデーションエラー**: 入力検証の例外は意図的に発生させてテスト
- **ビジネスロジックの分岐**: すべての条件分岐をテスト
- **エラーハンドリング**: 想定されるエラーケースはテスト
- **境界値**: 最小値、最大値、空のケースなど

## 実装例

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional

def divide(a: int, b: int) -> float:
    """2つの数値を除算する。"""
    if b == 0:
        raise ValueError("Cannot divide by zero")  # テストで検証する
    return a / b


def safe_divide(a: int, b: int) -> float | None:
    """安全に除算を行う。"""
    try:
        return divide(a, b)
    except ValueError:
        logger.warning(f"Division by zero attempted: {a}/{b}")
        return None
    except Exception as e:  # pragma: no cover
        logger.critical(f"Unexpected error in division: {e}")
        raise


if __name__ == "__main__":  # pragma: no cover
    result = divide(10, 2)
    print(f"Result: {result}")
```

## pyproject.toml でのカバレッジ設定

```toml
[tool.coverage.run]
source = ["src/study_python"]
branch = true
omit = [
    "*/__pycache__/*",
    "*/tests/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
    "raise NotImplementedError",
    "@abstractmethod",
]
fail_under = 90
show_missing = true
skip_covered = false

[tool.coverage.html]
directory = "htmlcov"
```

## 注意事項

- `# pragma: no cover` の乱用は禁止（レビューで確認）
- カバレッジ率が下がる変更はPRで理由を説明すること
- 新規ファイルは100%カバレッジを目指す
- レガシーコードは段階的にカバレッジを向上させる
