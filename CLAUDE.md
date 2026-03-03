# CLAUDE.md - ClaudeCode プロジェクト指示書

このファイルはClaudeCodeがプロジェクトを理解し、一貫した開発を行うための指示書です。

## プロジェクト概要

- **目的**: （プロジェクトの目的を記載する）
- **言語**: Python 3.12+
- **パッケージ管理**: uv（推奨）または pip

## ディレクトリ構造

```
.
├── CLAUDE.md           # このファイル（ClaudeCode用指示）
├── pyproject.toml      # プロジェクト設定・依存関係
├── src/                # ソースコード
│   └── study_python/   # メインパッケージ
├── tests/              # テストコード
├── docs/               # ドキュメント（必要に応じて）
├── scripts/            # ユーティリティスクリプト
└── logs/               # ログファイル（.gitignore対象）
```

## コーディング規約

### Python スタイルガイド

1. **PEP 8 準拠**: ruffによる自動フォーマット・リント
2. **型ヒント必須**: すべての関数に型アノテーションを付与
3. **docstring**: Google スタイルを使用

```python
def example_function(param1: str, param2: int) -> bool:
    """関数の説明を簡潔に記述する。

    Args:
        param1: 最初のパラメータの説明。
        param2: 2番目のパラメータの説明。

    Returns:
        戻り値の説明。

    Raises:
        ValueError: エラーが発生する条件の説明。
    """
    pass
```

### 命名規則

- **変数・関数**: snake_case（例: `user_name`, `calculate_total`）
- **クラス**: PascalCase（例: `UserAccount`, `DataProcessor`）
- **定数**: UPPER_SNAKE_CASE（例: `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`）
- **プライベート**: 先頭にアンダースコア（例: `_internal_method`）

### インポート順序

1. 標準ライブラリ
2. サードパーティライブラリ
3. ローカルモジュール

```python
import os
import sys
from pathlib import Path

import requests
from pydantic import BaseModel

from study_python.core import utils
```

## 開発コマンド

```bash
# 依存関係のインストール
uv sync

# リンター実行
uv run ruff check .

# フォーマッター実行
uv run ruff format .

# 型チェック
uv run mypy src/

# テスト実行
uv run pytest

# テスト（カバレッジ付き）
uv run pytest --cov=src/study_python --cov-report=html
```

## コミットメッセージ規約

[Conventional Commits](https://www.conventionalcommits.org/) に従う：

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `style`: コードの意味に影響しない変更（空白、フォーマット等）
- `refactor`: バグ修正でも機能追加でもないコード変更
- `test`: テストの追加・修正
- `chore`: ビルドプロセスやツールの変更

### 例

```
feat(auth): ユーザー認証機能を追加

- JWTトークンによる認証を実装
- ログイン/ログアウトAPIを追加

Closes #123
```

## テスト方針

1. **ユニットテスト**: 各関数・メソッドに対してテストを作成
2. **命名規則**: `test_<関数名>_<テスト条件>`
3. **配置**: `tests/` ディレクトリに `test_*.py` として配置
4. **Fixtures**: 共通のセットアップは `conftest.py` に定義

```python
# tests/test_calculator.py
import pytest
from study_python.calculator import add

def test_add_positive_numbers():
    assert add(1, 2) == 3

def test_add_negative_numbers():
    assert add(-1, -2) == -3

def test_add_with_zero():
    assert add(0, 5) == 5
```

### GUIテスト方針（重要）

GUIアプリケーションもユニットテストの対象とする。**GUIとロジックを分離**し、ロジック部分は必ずテストを作成すること。

#### アーキテクチャ原則

GUIコードは以下の構造で実装する：

```
┌─────────────────────────────────────────┐
│           GUI Layer (View)              │
│  - ウィジェット配置                      │
│  - イベントハンドラ                      │
│  - 表示更新                              │
└─────────────────────────────────────────┘
                    ↓ 呼び出し
┌─────────────────────────────────────────┐
│         Logic Layer (Controller)         │
│  - ビジネスロジック                      │
│  - データ処理                            │
│  - バリデーション                        │
│  ※ このレイヤーをユニットテスト対象     │
└─────────────────────────────────────────┘
                    ↓ 呼び出し
┌─────────────────────────────────────────┐
│          Data Layer (Model)              │
│  - データアクセス                        │
│  - 永続化処理                            │
└─────────────────────────────────────────┘
```

#### GUIロジック分離の実装例

```python
# src/study_python/gui/calculator_logic.py
# ロジック部分（テスト対象）

class CalculatorLogic:
    """計算機のビジネスロジック。"""

    def __init__(self) -> None:
        self.current_value: float = 0
        self.history: list[str] = []

    def add(self, value: float) -> float:
        """値を加算する。"""
        self.current_value += value
        self.history.append(f"+ {value}")
        return self.current_value

    def subtract(self, value: float) -> float:
        """値を減算する。"""
        self.current_value -= value
        self.history.append(f"- {value}")
        return self.current_value

    def clear(self) -> None:
        """リセットする。"""
        self.current_value = 0
        self.history.clear()

    def validate_input(self, value: str) -> float:
        """入力値を検証する。

        Raises:
            ValueError: 数値に変換できない場合。
        """
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Invalid number: {value}")
```

```python
# src/study_python/gui/calculator_gui.py
# GUI部分（ロジックを呼び出すのみ）

import tkinter as tk
from study_python.gui.calculator_logic import CalculatorLogic


class CalculatorGUI:
    """計算機のGUI。"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.logic = CalculatorLogic()  # ロジックを注入
        self._setup_widgets()

    def _setup_widgets(self) -> None:
        """ウィジェットを配置する。"""
        self.entry = tk.Entry(self.root)
        self.entry.pack()

        self.add_button = tk.Button(
            self.root, text="+", command=self._on_add_click
        )
        self.add_button.pack()

        self.result_label = tk.Label(self.root, text="0")
        self.result_label.pack()

    def _on_add_click(self) -> None:
        """加算ボタンのクリックハンドラ。"""
        try:
            value = self.logic.validate_input(self.entry.get())
            result = self.logic.add(value)
            self.result_label.config(text=str(result))
        except ValueError as e:
            self.result_label.config(text=f"Error: {e}")
```

#### GUIロジックのテスト例

```python
# tests/gui/test_calculator_logic.py
import pytest
from study_python.gui.calculator_logic import CalculatorLogic


class TestCalculatorLogic:
    """CalculatorLogicのテスト。"""

    def test_add_positive_value(self):
        """正の値の加算テスト。"""
        logic = CalculatorLogic()
        result = logic.add(5)
        assert result == 5
        assert logic.current_value == 5

    def test_add_multiple_values(self):
        """複数回の加算テスト。"""
        logic = CalculatorLogic()
        logic.add(5)
        result = logic.add(3)
        assert result == 8

    def test_subtract(self):
        """減算テスト。"""
        logic = CalculatorLogic()
        logic.add(10)
        result = logic.subtract(3)
        assert result == 7

    def test_clear(self):
        """リセットテスト。"""
        logic = CalculatorLogic()
        logic.add(10)
        logic.clear()
        assert logic.current_value == 0
        assert logic.history == []

    def test_validate_input_valid(self):
        """有効な入力値のテスト。"""
        logic = CalculatorLogic()
        assert logic.validate_input("123") == 123.0
        assert logic.validate_input("45.67") == 45.67
        assert logic.validate_input("-10") == -10.0

    def test_validate_input_invalid(self):
        """無効な入力値のテスト。"""
        logic = CalculatorLogic()
        with pytest.raises(ValueError, match="Invalid number"):
            logic.validate_input("abc")

    def test_history_tracking(self):
        """履歴追跡のテスト。"""
        logic = CalculatorLogic()
        logic.add(5)
        logic.subtract(2)
        assert logic.history == ["+ 5", "- 2"]
```

#### GUIフレームワーク別のテスト方法

| フレームワーク | テストライブラリ | 用途 |
|---------------|-----------------|------|
| Tkinter | `unittest.mock` | イベントのモック |
| PyQt/PySide | `pytest-qt` | Qtウィジェットのテスト |
| Kivy | `pytest` + モック | イベント・状態のテスト |
| wxPython | `unittest.mock` | イベントのモック |

#### pytest-qt を使用したGUIテスト例（PyQt/PySide）

```python
# tests/gui/test_calculator_gui_qt.py
import pytest
from pytestqt.qtbot import QtBot
from PySide6.QtCore import Qt
from study_python.gui.calculator_gui_qt import CalculatorWindow


@pytest.fixture
def calculator(qtbot: QtBot) -> CalculatorWindow:
    """計算機ウィンドウのフィクスチャ。"""
    window = CalculatorWindow()
    qtbot.addWidget(window)
    return window


def test_add_button_click(calculator: CalculatorWindow, qtbot: QtBot):
    """加算ボタンクリックのテスト。"""
    calculator.input_field.setText("5")
    qtbot.mouseClick(calculator.add_button, Qt.LeftButton)
    assert calculator.result_label.text() == "5"


def test_invalid_input_shows_error(calculator: CalculatorWindow, qtbot: QtBot):
    """無効入力時のエラー表示テスト。"""
    calculator.input_field.setText("abc")
    qtbot.mouseClick(calculator.add_button, Qt.LeftButton)
    assert "Error" in calculator.result_label.text()
```

#### テストディレクトリ構成

```
tests/
├── conftest.py              # 共通フィクスチャ
├── test_calculator.py       # 通常のユニットテスト
└── gui/                     # GUIテスト専用ディレクトリ
    ├── __init__.py
    ├── conftest.py          # GUI用フィクスチャ
    ├── test_calculator_logic.py   # ロジックのテスト
    └── test_calculator_gui.py     # GUI統合テスト（オプション）
```

#### GUIテストのルール

1. **ロジック分離必須**: GUIからビジネスロジックを分離する
2. **ロジックは100%カバレッジ**: 分離したロジックは通常のユニットテスト対象
3. **GUI層は最小限**: GUI層はロジック呼び出しと表示更新のみ
4. **依存性注入**: ロジッククラスはGUIクラスに注入可能にする
5. **モックの活用**: 外部依存はモックで置き換える

#### 禁止事項

- GUIクラス内にビジネスロジックを直接記述すること
- ロジック部分のテストを省略すること
- GUIイベントハンドラ内で複雑な処理を行うこと

## カバレッジ方針（重要）

コードの品質を保証するため、テストカバレッジ率100%を目指す。

### 目標

- **カバレッジ率**: 100%（除外対象を除く）
- **必須**: 新規コードには必ずテストを作成する
- **CI/CD**: カバレッジが基準を下回る場合はマージをブロック

### カバレッジ実行コマンド

```bash
# カバレッジ付きテスト実行
uv run pytest --cov=src/study_python --cov-report=html --cov-report=term-missing

# カバレッジレポートの確認
# htmlcov/index.html をブラウザで開く
```

### カバレッジ除外の方法

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

### 除外してよいケース

以下のケースのみ `# pragma: no cover` の使用を許可する：

| ケース | 理由 | 例 |
|--------|------|-----|
| 予期しない例外ハンドラ | 防御的コードで通常到達しない | `except Exception:` |
| デバッグ専用コード | 本番では実行されない | `if DEBUG:` ブロック |
| 抽象メソッド | 実装クラスでテストする | `raise NotImplementedError` |
| 型チェック専用ブロック | 実行時には不要 | `if TYPE_CHECKING:` |
| プラットフォーム固有コード | 実行環境で到達不可 | `if sys.platform == 'win32':` |
| main実行ブロック | モジュールとして使用時は不要 | `if __name__ == '__main__':` |

### 除外してはいけないケース

以下は必ずテストでカバーすること：

- **バリデーションエラー**: 入力検証の例外は意図的に発生させてテスト
- **ビジネスロジックの分岐**: すべての条件分岐をテスト
- **エラーハンドリング**: 想定されるエラーケースはテスト
- **境界値**: 最小値、最大値、空のケースなど

### 実装例

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional

def divide(a: int, b: int) -> float:
    """2つの数値を除算する。

    Args:
        a: 被除数。
        b: 除数。

    Returns:
        除算結果。

    Raises:
        ValueError: 除数が0の場合。
    """
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
        # 予期しないエラー（通常到達しない防御的コード）
        logger.critical(f"Unexpected error in division: {e}")
        raise


if __name__ == "__main__":  # pragma: no cover
    # スクリプトとして直接実行時のみ
    result = divide(10, 2)
    print(f"Result: {result}")
```

### テストでのカバレッジ確保

```python
# tests/test_divide.py
import pytest
from study_python.math_utils import divide, safe_divide


def test_divide_normal():
    """正常な除算のテスト。"""
    assert divide(10, 2) == 5.0


def test_divide_by_zero():
    """ゼロ除算エラーのテスト。"""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)


def test_safe_divide_normal():
    """safe_divideの正常系テスト。"""
    assert safe_divide(10, 2) == 5.0


def test_safe_divide_by_zero():
    """safe_divideのゼロ除算テスト。"""
    result = safe_divide(10, 0)
    assert result is None
```

### pyproject.toml でのカバレッジ設定

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

### 注意事項

- `# pragma: no cover` の乱用は禁止（レビューで確認）
- カバレッジ率が下がる変更はPRで理由を説明すること
- 新規ファイルは100%カバレッジを目指す
- レガシーコードは段階的にカバレッジを向上させる

## エラーハンドリング

1. **具体的な例外**: 汎用的な `Exception` ではなく具体的な例外を使用
2. **カスタム例外**: 必要に応じてドメイン固有の例外を定義
3. **ログ出力**: エラー時は適切なログレベルで記録

```python
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """入力検証エラー"""
    pass

def process_data(data: dict) -> None:
    try:
        validate(data)
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        raise
```

## セキュリティ注意事項

- 機密情報（APIキー、パスワード等）はコードにハードコードしない
- 環境変数または `.env` ファイル（.gitignoreに含める）を使用
- ユーザー入力は必ずバリデーション・サニタイズを行う

## ログ出力ルール（重要）

すべてのツール・モジュールには、ユーザーからの問い合わせ対応（特に不具合調査）のためにログ出力機能を実装すること。

### 必須事項

1. **ログ出力の実装**: すべてのモジュールで `logging` を使用する
2. **ファイル出力**: ログはリポジトリ内の `logs/` ディレクトリに保存する
3. **適切なログレベル**: 状況に応じたログレベルを使用する

### ログレベルの使い分け

| レベル | 用途 |
|--------|------|
| `DEBUG` | 開発時のデバッグ情報（変数値、処理フロー等） |
| `INFO` | 正常な処理の記録（開始、終了、重要なステップ） |
| `WARNING` | 注意が必要だが処理は継続可能な状況 |
| `ERROR` | エラー発生（処理失敗、例外キャッチ等） |
| `CRITICAL` | システム停止レベルの重大エラー |

### ログ設定の実装

プロジェクト共通のログ設定モジュールを使用する：

```python
# src/study_python/logging_config.py を使用
from study_python.logging_config import setup_logging

# モジュール初期化時にログ設定を適用
setup_logging()

# 各モジュールでロガーを取得
import logging
logger = logging.getLogger(__name__)
```

### ログフォーマット

デバッグしやすいフォーマットを使用：

```
2024-01-15 10:30:45.123 | INFO     | module_name:function_name:42 | メッセージ
```

フォーマット要素：
- **タイムスタンプ**: ミリ秒まで記録
- **ログレベル**: 見やすく固定幅
- **モジュール名**: 問題箇所の特定用
- **関数名・行番号**: デバッグ時の追跡用
- **メッセージ**: 具体的な内容

### 実装例

```python
import logging
from study_python.logging_config import setup_logging

# ログ設定を適用
setup_logging()
logger = logging.getLogger(__name__)

def process_user_data(user_id: int, data: dict) -> bool:
    """ユーザーデータを処理する。"""
    logger.info(f"Processing data for user_id={user_id}")
    logger.debug(f"Input data: {data}")

    try:
        # 処理実行
        result = validate_and_save(data)
        logger.info(f"Successfully processed user_id={user_id}")
        return result
    except ValidationError as e:
        logger.error(f"Validation failed for user_id={user_id}: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error for user_id={user_id}: {e}", exc_info=True)
        raise
```

### ログファイル管理

- **保存先**: リポジトリルートの `logs/` ディレクトリ（.gitignoreに含める）
- **ファイル名**: `app_YYYY-MM-DD.log`（日付ローテーション）
- **保持期間**: 30日間（古いログは自動削除）
- **最大サイズ**: 10MB（サイズローテーション）

### 注意事項

- 機密情報（パスワード、トークン等）はログに出力しない
- 大量データはログに出力せず、件数やサマリーを記録する
- 本番環境では `INFO` 以上、開発環境では `DEBUG` 以上を出力する

## ドキュメント管理（重要）

プログラムの作成・変更を行った際は、必ず関連ドキュメントを最新化すること。

### 必須ドキュメント

| ドキュメント | 配置場所 | 更新タイミング |
|-------------|---------|---------------|
| README.md | プロジェクトルート | 機能追加・変更時 |
| 設計書 | `docs/design/` | アーキテクチャ変更時 |
| 仕様書 | `docs/specs/` | 機能仕様変更時 |
| 要件定義書 | `docs/requirements/` | 要件追加・変更時 |
| API仕様書 | `docs/api/` | API変更時 |
| CHANGELOG.md | プロジェクトルート | リリース時 |

### README.md 更新ルール

README.mdには以下の情報を常に最新の状態で維持する：

1. **プロジェクト概要**: 目的と主要機能の説明
2. **インストール方法**: 依存関係とセットアップ手順
3. **使用方法**: 基本的な使い方とコード例
4. **設定**: 環境変数や設定ファイルの説明
5. **コマンド一覧**: 利用可能なコマンドとオプション

### 設計書・仕様書の更新ルール

#### 更新が必要なケース

- **新機能追加**: 機能の目的、設計、インターフェースを文書化
- **既存機能の変更**: 変更内容と影響範囲を更新
- **アーキテクチャ変更**: システム構成図、データフロー図を更新
- **API変更**: エンドポイント、リクエスト/レスポンス仕様を更新
- **データベース変更**: スキーマ、ER図を更新

#### ドキュメント構成例

```
docs/
├── design/
│   ├── architecture.md      # システムアーキテクチャ
│   ├── database.md          # データベース設計
│   └── diagrams/            # 図表（PlantUML、Mermaid等）
├── specs/
│   ├── feature_xxx.md       # 機能仕様書
│   └── api_spec.md          # API仕様書
├── requirements/
│   ├── functional.md        # 機能要件
│   └── non_functional.md    # 非機能要件
└── guides/
    ├── development.md       # 開発ガイド
    └── deployment.md        # デプロイガイド
```

### ドキュメント記載ルール

1. **日付の記録**: 更新日を必ず記載する
2. **変更履歴**: 重要な変更は履歴として残す
3. **図表の活用**: 複雑な処理はフローチャートやシーケンス図で説明
4. **コード例**: 使用方法は具体的なコード例を含める
5. **用語の統一**: プロジェクト内で用語を統一する

### Mermaid図表の例

```markdown
## シーケンス図

​```mermaid
sequenceDiagram
    participant User
    participant API
    participant Database

    User->>API: リクエスト
    API->>Database: クエリ
    Database-->>API: 結果
    API-->>User: レスポンス
​```
```

### チェックリスト

コード変更時は以下を確認すること：

- [ ] README.mdの内容は最新か
- [ ] 新機能の仕様書は作成したか
- [ ] 既存の設計書に影響はないか
- [ ] APIの変更はAPI仕様書に反映したか
- [ ] 図表（アーキテクチャ図等）の更新は必要か
- [ ] CHANGELOGに変更内容を追記したか

### 注意事項

- ドキュメントの更新を忘れた場合、PRレビューで指摘すること
- 古いドキュメントは混乱の元になるため、常に最新化を優先する
- ドキュメントが存在しない場合は新規作成する
- 不要になったドキュメントは削除または非推奨マークを付ける

## ClaudeCode 使用時の注意

1. **変更前に確認**: ファイルを編集する前に必ず内容を確認する
2. **小さな変更**: 大きな変更は小さなステップに分割する
3. **テスト実行**: コード変更後は必ずテストを実行する（下記参照）
4. **既存コードの尊重**: プロジェクトの既存パターンに従う

### テスト自動実行ルール（必須）

**プログラムを修正した際は、必ずユニットテストを実行すること。**

#### 実行タイミング

以下の変更を行った場合、**必ず**テストを実行する：

- `src/` 配下のPythonファイルを新規作成・修正した場合
- `tests/` 配下のテストファイルを新規作成・修正した場合
- `pyproject.toml` の依存関係を変更した場合
- 設定ファイル（`.env`等）を変更した場合

#### 実行コマンド

```bash
# 基本のテスト実行
uv run pytest

# カバレッジ付きテスト実行（推奨）
uv run pytest --cov=src/study_python --cov-report=term-missing

# 特定のテストファイルのみ実行
uv run pytest tests/test_specific.py -v

# 失敗したテストのみ再実行
uv run pytest --lf
```

#### テスト実行フロー

```
コード修正
    ↓
テスト実行 (uv run pytest)
    ↓
┌─────────────────┐
│ テスト結果確認   │
└─────────────────┘
    ↓           ↓
  成功         失敗
    ↓           ↓
  完了      原因調査・修正
              ↓
           再テスト
```

#### テスト失敗時の自動修正ルール（必須）

**テストが失敗した場合、ClaudeCodeは自動的に原因調査と修正を行うこと。**

##### 自動修正フロー

```
テスト失敗検出
    ↓
┌─────────────────────────────────┐
│ 1. エラーメッセージの解析        │
│    - 失敗したテスト名を特定      │
│    - エラータイプを確認          │
│    - スタックトレースを解析      │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 2. 原因の特定                    │
│    - 該当ソースコードを読む      │
│    - テストコードを確認          │
│    - 期待値と実際の値を比較      │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 3. 修正の実施                    │
│    - ソースコードを修正          │
│    - または テストを修正         │
│    - 修正内容をログに記録        │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 4. 再テスト実行                  │
│    - 全テストを再実行            │
│    - 成功するまで繰り返す        │
└─────────────────────────────────┘
    ↓
  全テスト成功 → 完了
```

##### エラータイプ別の対応方針

| エラータイプ | 原因 | 対応方法 |
|-------------|------|---------|
| `AssertionError` | 期待値と実際の値が不一致 | ロジックを確認し、ソースまたはテストを修正 |
| `ImportError` | モジュールが見つからない | インポートパスを確認・修正 |
| `AttributeError` | 属性・メソッドが存在しない | クラス定義を確認・修正 |
| `TypeError` | 型の不一致 | 引数の型を確認・修正 |
| `ValueError` | 不正な値 | バリデーションロジックを確認 |
| `KeyError` | 辞書キーが存在しない | キーの存在確認を追加 |
| `FileNotFoundError` | ファイルが見つからない | パスを確認・テストフィクスチャを修正 |

##### 修正の優先順位

1. **ソースコードのバグ修正**: 明らかなバグがある場合
2. **テストの期待値修正**: 仕様変更に伴う場合
3. **テストフィクスチャの修正**: テストデータの問題の場合
4. **モックの追加・修正**: 外部依存の問題の場合

##### 自動修正の実行例

```python
# テスト失敗例
# FAILED tests/test_calculator.py::test_add - AssertionError: assert 5 == 4

# 1. エラー解析
#    - test_add が失敗
#    - 期待値: 4, 実際の値: 5

# 2. 原因特定
#    - calculator.py の add 関数を確認
#    - テストコードの期待値を確認

# 3. 修正実施（ソースコードにバグがある場合）
def add(a: int, b: int) -> int:
    return a + b  # 修正: a + b + 1 → a + b

# 4. 再テスト実行
#    uv run pytest tests/test_calculator.py -v
```

##### 修正時の注意事項

- **最小限の修正**: 失敗の原因となっている箇所のみ修正する
- **他への影響確認**: 修正が他のテストに影響しないか確認する
- **修正理由の記録**: なぜその修正を行ったかをコメントで説明する
- **繰り返し上限**: 同じエラーが3回続く場合はユーザーに報告する

##### 自動修正できないケース

以下の場合はユーザーに確認を求める：

- 仕様の解釈が曖昧な場合
- 複数の修正方法が考えられる場合
- 外部サービスへの接続が必要な場合
- セキュリティに関わる修正の場合
- 大規模なリファクタリングが必要な場合

#### 禁止事項

- テストを実行せずにコミットすること
- 失敗するテストを無視してコミットすること
- テストをスキップ（`@pytest.mark.skip`）して問題を回避すること
- カバレッジが下がる変更を理由なく行うこと

#### テスト実行の自動化

ClaudeCodeは以下のワークフローを必ず守ること：

```
1. コード修正を完了
2. uv run pytest を実行
3. 結果を確認
4. 失敗があれば修正して再実行
5. 全テスト成功を確認してから次の作業へ
```
