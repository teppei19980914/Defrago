# プロジェクト名

プロジェクトの概要を記載してください。

## 必要条件

- Python 3.12 以上
- [uv](https://docs.astral.sh/uv/)（推奨）または pip

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-username/your-project.git
cd your-project
```

### 2. 依存関係のインストール

**uv を使用する場合（推奨）:**

```bash
# uv のインストール（未インストールの場合）
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係のインストール
uv sync --dev
```

**pip を使用する場合:**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

### 3. pre-commit フックのインストール

```bash
uv run pre-commit install
```

## 開発コマンド

```bash
# リンターの実行
uv run ruff check .

# フォーマッターの実行
uv run ruff format .

# 型チェック
uv run mypy src/

# テストの実行
uv run pytest

# テスト（カバレッジ付き）
uv run pytest --cov=src/study_python --cov-report=html

# pre-commit の手動実行
uv run pre-commit run --all-files
```

## バッチスクリプト

`scripts/` フォルダにWindows(.bat)とUnix(.sh)両対応のスクリプトを用意しています。

**すべてのスクリプトは実行時に依存関係を自動インストールします。**
手動で `uv sync` を実行する必要はありません。

### テスト実行（用途別）

| スクリプト | 用途 | 速度 |
|-----------|------|------|
| `test.bat` / `test.sh` | 開発中の頻繁なテスト | 高速 |
| `test-full.bat` / `test-full.sh` | カバレッジ確認・レビュー前 | 通常 |

```bash
# 高速テスト（開発中に使用）
scripts\test.bat              # Windows
./scripts/test.sh             # Unix/macOS

# カバレッジ付きテスト（コミット前・レビュー時）
scripts\test-full.bat         # Windows
./scripts/test-full.sh        # Unix/macOS

# オプション（すべてのスクリプトで共通）
--verbose       # 詳細出力
--fast          # 最初の失敗で停止
--skip-install  # 依存関係のインストールをスキップ（高速化）
```

### リント・フォーマット

```bash
# Windows
scripts\lint.bat

# Unix/macOS
./scripts/lint.sh

# オプション
--fix           # 自動修正を適用
--check         # チェックのみ（デフォルト）
--skip-install  # 依存関係のインストールをスキップ
```

### 全チェック（リント + 型チェック + テスト）

```bash
# Windows
scripts\check-all.bat

# Unix/macOS
./scripts/check-all.sh

# オプション
--fix           # リント・フォーマットを自動修正
--cov           # カバレッジを取得
--skip-install  # 依存関係のインストールをスキップ
```

### カバレッジレポートの確認

`test-full.bat` または `check-all.bat --cov` 実行後、
`htmlcov/index.html` をブラウザで開くと：

- ファイルごとのカバレッジ率
- カバーされていない行のハイライト表示
- 全体のカバレッジサマリー

が確認できます。

## プロジェクト構造

```
.
├── CLAUDE.md               # ClaudeCode 用プロジェクト指示
├── README.md               # このファイル
├── pyproject.toml          # プロジェクト設定
├── .python-version         # Python バージョン指定
├── .editorconfig           # エディタ設定
├── .pre-commit-config.yaml # pre-commit 設定
├── .vscode/                # VSCode 共有設定
│   ├── settings.json       # エディタ設定
│   └── extensions.json     # 推奨拡張機能
├── scripts/                # ユーティリティスクリプト
│   ├── test.bat / test.sh        # テスト実行（高速）
│   ├── test-full.bat / test-full.sh  # テスト実行（カバレッジ付き）
│   ├── lint.bat / lint.sh        # リント・フォーマット
│   └── check-all.bat / check-all.sh  # 全チェック
├── src/
│   └── study_python/       # メインパッケージ
│       ├── __init__.py
│       ├── calculator.py      # サンプルモジュール
│       ├── logging_config.py  # ログ設定モジュール
│       └── py.typed           # PEP 561 マーカー
├── tests/                  # テストコード
│   ├── __init__.py
│   ├── conftest.py              # pytest フィクスチャ
│   ├── test_calculator.py       # サンプルテスト
│   └── test_logging_config.py   # ログ設定テスト
└── logs/                   # ログファイル（.gitignore対象）
```

## VSCode 拡張機能

このプロジェクトを VSCode で開くと、推奨拡張機能のインストールを促されます。
以下の拡張機能がチーム開発に役立ちます：

- **Python** - Python 言語サポート
- **Pylance** - 高速な型チェックと補完
- **Ruff** - リンター＆フォーマッター
- **EditorConfig** - エディタ設定の統一
- **GitLens** - Git 履歴の可視化

## ログ機能

本プロジェクトでは、デバッグや問い合わせ対応のためにログ出力機能を標準で実装しています。

### 基本的な使い方

```python
from study_python.logging_config import setup_logging, get_logger

# アプリケーション起動時にログ設定を初期化
setup_logging()

# モジュールごとにロガーを取得
logger = get_logger(__name__)

# ログ出力
logger.debug("デバッグ情報")
logger.info("処理開始")
logger.warning("警告メッセージ")
logger.error("エラー発生")
```

### ログレベル

| レベル | 用途 |
|--------|------|
| `DEBUG` | 開発時のデバッグ情報 |
| `INFO` | 正常な処理の記録 |
| `WARNING` | 注意が必要な状況 |
| `ERROR` | エラー発生 |
| `CRITICAL` | 重大なエラー |

### ログファイルの保存先

- **ディレクトリ**: `logs/`
- **ファイル名**: `app_YYYY-MM-DD.log`（日付ローテーション）
- **保持期間**: 30日間
- **最大サイズ**: 10MB（サイズローテーション）

### 設定のカスタマイズ

```python
from study_python.logging_config import setup_logging

# ログレベルを変更
setup_logging(level="DEBUG")

# コンソール出力のみ（ファイル出力なし）
setup_logging(log_to_file=False)

# カスタムログディレクトリ
setup_logging(log_dir="/path/to/logs")
```

詳細な実装ルールは [CLAUDE.md](CLAUDE.md) の「ログ出力ルール」セクションを参照してください。

## コーディング規約

詳細は [CLAUDE.md](CLAUDE.md) を参照してください。

### 主なルール

- **PEP 8 準拠**: ruff による自動フォーマット
- **型ヒント必須**: すべての関数に型アノテーション
- **docstring**: Google スタイル
- **テスト**: pytest を使用

### コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) 形式に従います：

```
feat: 新機能
fix: バグ修正
docs: ドキュメント変更
style: フォーマット変更
refactor: リファクタリング
test: テスト追加・修正
chore: ビルド・ツール変更
```

---

## 設定ファイルリファレンス

このセクションでは、各設定ファイルの項目について詳細に説明します。
テンプレートとして使用する際の参考にしてください。

### pyproject.toml

Python プロジェクトの中心的な設定ファイルです。PEP 621 に準拠しています。

#### [project] セクション - プロジェクト基本情報

| 設定項目 | 現在の値 | 説明 | 変更例 |
|---------|---------|------|--------|
| `name` | `"study-python"` | パッケージ名（pip install時の名前） | `"my-awesome-project"` |
| `version` | `"0.1.0"` | バージョン番号（[セマンティックバージョニング](https://semver.org/)推奨） | `"1.0.0"`, `"2.1.3"` |
| `description` | `"PythonとClaudeCode..."` | パッケージの簡潔な説明 | 任意の説明文 |
| `readme` | `"README.md"` | READMEファイルのパス | `"docs/README.md"` |
| `requires-python` | `">=3.12"` | 必要なPythonバージョン | `">=3.10"`, `">=3.11,<3.13"` |
| `license` | `{ text = "MIT" }` | ライセンス種別 | `"Apache-2.0"`, `"GPL-3.0"` |
| `authors` | `[{ name = "...", email = "..." }]` | 著者情報 | 自分の情報に変更 |
| `keywords` | `["python", "learning", ...]` | PyPIでの検索用キーワード | プロジェクトに関連するキーワード |
| `classifiers` | `[...]` | [PyPI分類子](https://pypi.org/classifiers/) | 開発状況やライセンスに応じて変更 |

#### [project.optional-dependencies] セクション - オプション依存関係

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",      # テストフレームワーク
    "pytest-cov>=4.1.0",  # カバレッジ計測
    "mypy>=1.8.0",        # 型チェッカー
    "ruff>=0.4.0",        # リンター＆フォーマッター
    "pre-commit>=3.6.0",  # コミット前フック
]
```

- `>=8.0.0`: バージョン8.0.0以上を要求
- 新しい依存関係を追加する場合はこのリストに追記
- インストール: `uv sync --dev` または `pip install -e ".[dev]"`

#### [build-system] セクション - ビルド設定

```toml
[build-system]
requires = ["hatchling"]        # ビルドに必要なパッケージ
build-backend = "hatchling.build"  # 使用するビルドバックエンド
```

他のビルドバックエンドの選択肢:
- `setuptools` - 伝統的な選択肢
- `flit_core.flit_backend` - シンプルなプロジェクト向け
- `poetry-core.masonry.api` - Poetry使用時

#### [tool.hatch.build.targets.wheel] セクション

```toml
packages = ["src/study_python"]  # wheelに含めるパッケージのパス
```

- `src/` レイアウトを使用する場合に必要
- パッケージ名を変更した場合はここも更新

#### [tool.ruff] セクション - Ruff設定

```toml
[tool.ruff]
target-version = "py312"  # ターゲットPythonバージョン（py310, py311, py312, py313）
line-length = 88          # 1行の最大文字数（79, 88, 100, 120が一般的）
src = ["src", "tests"]    # ソースコードのディレクトリ
```

#### [tool.ruff.lint] セクション - リントルール

| ルールコード | 名前 | 説明 | 無効化の影響 |
|-------------|------|------|-------------|
| `E` | pycodestyle errors | PEP 8 エラー | 基本的なスタイル違反を見逃す |
| `W` | pycodestyle warnings | PEP 8 警告 | 軽微なスタイル問題を見逃す |
| `F` | Pyflakes | 未使用変数・インポートなど | バグの原因を見逃す可能性 |
| `I` | isort | インポート順序 | インポートの整理が自動化されない |
| `B` | flake8-bugbear | バグになりやすいパターン | 潜在的なバグを見逃す |
| `C4` | flake8-comprehensions | 内包表記の最適化 | 非効率なコードが残る |
| `UP` | pyupgrade | 古いPython構文の検出 | レガシー構文が残る |
| `ARG` | flake8-unused-arguments | 未使用引数 | 不要な引数が残る |
| `SIM` | flake8-simplify | コード簡略化 | 冗長なコードが残る |
| `TCH` | flake8-type-checking | TYPE_CHECKING最適化 | ランタイムの無駄なインポート |
| `PTH` | flake8-use-pathlib | pathlib推奨 | os.path使用が残る |
| `ERA` | eradicate | コメントアウトコード検出 | 不要なコメントが残る |
| `PL` | Pylint | 包括的なチェック | 様々な問題を見逃す |
| `RUF` | Ruff-specific | Ruff独自ルール | Ruff特有の最適化を見逃す |

#### [tool.ruff.lint] ignore設定

```toml
ignore = [
    "E501",    # 行長超過（フォーマッターが処理するため無視）
    "PLR0913", # 引数が多すぎる（必要な場合があるため無視）
    "PLR2004", # マジックナンバー比較（定数化が過度になるため無視）
]
```

特定ルールを無視したい場合はここに追加。

#### [tool.ruff.lint.per-file-ignores] - ファイル別の無視設定

```toml
"tests/**/*.py" = [
    "ARG",     # テストではfixtureで未使用引数が発生する
    "PLR2004", # テストではマジックナンバーが許容される
]
```

特定のディレクトリ・ファイルでのみルールを無視したい場合に使用。

#### [tool.ruff.lint.isort] - インポートソート設定

```toml
known-first-party = ["study_python"]  # プロジェクトのパッケージ名
force-single-line = false             # true: 各インポートを1行に
lines-after-imports = 2               # インポート後の空行数
```

#### [tool.ruff.format] - フォーマッター設定

| 設定項目 | 現在の値 | 説明 | 選択肢 |
|---------|---------|------|--------|
| `quote-style` | `"double"` | 文字列のクォート | `"single"`, `"double"` |
| `indent-style` | `"space"` | インデント文字 | `"space"`, `"tab"` |
| `skip-magic-trailing-comma` | `false` | 末尾カンマの保持 | `true`, `false` |
| `line-ending` | `"auto"` | 改行コード | `"auto"`, `"lf"`, `"crlf"` |
| `docstring-code-format` | `true` | docstring内コードのフォーマット | `true`, `false` |

#### [tool.mypy] セクション - 型チェック設定

```toml
[tool.mypy]
python_version = "3.12"         # チェック対象のPythonバージョン
strict = true                   # 厳格モード（以下の設定を一括有効化）
warn_return_any = true          # Any型の戻り値に警告
warn_unused_ignores = true      # 不要な# type: ignoreに警告
disallow_untyped_defs = true    # 型なし関数定義を禁止
disallow_incomplete_defs = true # 不完全な型定義を禁止
check_untyped_defs = true       # 型なし関数内もチェック
disallow_any_generics = true    # 型引数なしのジェネリクスを禁止
no_implicit_optional = true     # 暗黙のOptionalを禁止
warn_redundant_casts = true     # 不要なキャストに警告
warn_unused_configs = true      # 未使用の設定に警告
show_error_codes = true         # エラーコードを表示
show_column_numbers = true      # 列番号を表示
```

**厳格度の調整:**
- 緩くする: `strict = false` にして個別設定を削除
- 特定モジュールのみ緩和: `[[tool.mypy.overrides]]` を使用

#### [tool.pytest.ini_options] セクション - テスト設定

```toml
testpaths = ["tests"]                    # テストファイルの検索先
python_files = ["test_*.py", "*_test.py"] # テストファイルのパターン
python_classes = ["Test*"]               # テストクラスのパターン
python_functions = ["test_*"]            # テスト関数のパターン
addopts = [
    "-v",              # 詳細出力
    "--strict-markers", # 未定義マーカーをエラーに
    "--tb=short",      # トレースバックを短縮
]
markers = [
    "slow: ...",       # カスタムマーカー定義
    "integration: ...",
]
```

**addoptsの有用なオプション:**
- `-x`: 最初のエラーで停止
- `-s`: print出力を表示
- `--pdb`: エラー時にデバッガ起動
- `-k "test_name"`: 特定テストのみ実行

#### [tool.coverage] セクション - カバレッジ設定

```toml
[tool.coverage.run]
source = ["src/study_python"]  # カバレッジ計測対象
branch = true                  # 分岐カバレッジを計測
omit = ["*/tests/*", ...]      # 除外パターン

[tool.coverage.report]
fail_under = 80      # カバレッジがこの値未満でエラー
show_missing = true  # カバーされていない行を表示
exclude_lines = [    # カバレッジ計測から除外する行
    "pragma: no cover",
    "if TYPE_CHECKING:",
    # ...
]
```

---

### .editorconfig

エディタ間で一貫したスタイルを維持するための設定ファイル。

```ini
root = true  # このファイルがルート設定であることを示す

[*]  # すべてのファイルに適用
charset = utf-8                    # 文字エンコーディング
end_of_line = lf                   # 改行コード（lf, crlf, cr）
indent_style = space               # インデント（space, tab）
indent_size = 4                    # インデント幅
insert_final_newline = true        # ファイル末尾に改行を挿入
trim_trailing_whitespace = true    # 行末の空白を削除

[*.py]
max_line_length = 88  # Pythonファイルの最大行長

[*.{yml,yaml}]
indent_size = 2       # YAMLは2スペース

[*.md]
trim_trailing_whitespace = false  # Markdownでは末尾空白を保持（改行表現のため）

[Makefile]
indent_style = tab    # Makefileはタブ必須
```

**グロブパターンの例:**
- `*.py` - Pythonファイル
- `*.{js,ts}` - JSとTSファイル
- `lib/**.js` - libディレクトリ以下のすべてのJSファイル

---

### .pre-commit-config.yaml

コミット前に自動実行されるチェックの設定。

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0  # 使用するバージョン（定期的に更新推奨）
    hooks:
      - id: trailing-whitespace     # 行末空白を削除
        args: [--markdown-linebreak-ext=md]  # MDは例外
      - id: end-of-file-fixer       # ファイル末尾に改行を追加
      - id: check-yaml              # YAML構文チェック
      - id: check-toml              # TOML構文チェック
      - id: check-json              # JSON構文チェック
      - id: check-added-large-files # 大きなファイルの追加を防止
        args: ["--maxkb=1000"]      # 1MB以上でエラー
      - id: check-merge-conflict    # マージコンフリクトマーカーを検出
      - id: detect-private-key      # 秘密鍵の誤コミットを防止
      - id: mixed-line-ending       # 改行コードの混在を修正
        args: ["--fix=lf"]          # LFに統一
```

#### Ruff フック

```yaml
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff                    # リンター
        args: [--fix, --exit-non-zero-on-fix]  # 自動修正 & 修正があればエラー
      - id: ruff-format             # フォーマッター
```

#### MyPy フック

```yaml
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: []  # 追加の型スタブ（例: types-requests）
        args: [--config-file=pyproject.toml]
        pass_filenames: false        # ファイル名を渡さない
        entry: mypy src/             # srcディレクトリ全体をチェック
```

#### Conventional Commits フック

```yaml
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.2.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]  # コミットメッセージ時に実行
        args: [feat, fix, docs, style, refactor, test, chore, build, ci, perf, revert]
        # 許可するプレフィックス
```

#### CI設定

```yaml
ci:
  autofix_commit_msg: "style: auto-fix by pre-commit hooks"  # 自動修正時のコミットメッセージ
  autofix_prs: true          # PRで自動修正を実行
  autoupdate_commit_msg: "chore: update pre-commit hooks"    # フック更新時のメッセージ
  autoupdate_schedule: weekly  # 自動更新の頻度
```

---

### .python-version

pyenvやuvが使用するPythonバージョン指定ファイル。

```
3.12
```

- 使用するPythonバージョンを記載
- `uv` はこのファイルを読んで適切なPythonを使用
- 複数バージョンを指定可能: `3.12\n3.11`（改行区切り）

---

### .vscode/settings.json

VSCode のワークスペース設定。チーム全体で共有される。

#### Python設定

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    // Pythonインタープリタのパス
    // macOS/Linux: "${workspaceFolder}/.venv/bin/python"

    "python.analysis.typeCheckingMode": "basic",
    // 型チェックモード: "off", "basic", "standard", "strict"

    "python.analysis.autoImportCompletions": true,
    // 自動インポート補完を有効化

    "python.analysis.inlayHints.functionReturnTypes": true,
    // 関数の戻り値型をインラインヒントで表示

    "python.analysis.inlayHints.variableTypes": true
    // 変数の型をインラインヒントで表示
}
```

#### エディタ設定

```json
{
    "editor.formatOnSave": true,
    // 保存時に自動フォーマット

    "editor.codeActionsOnSave": {
        "source.fixAll": "explicit",
        // 保存時に自動修正を実行
        "source.organizeImports": "explicit"
        // 保存時にインポートを整理
    },

    "editor.rulers": [88],
    // 88文字位置にルーラーを表示

    "editor.tabSize": 4,
    // タブサイズ

    "editor.insertSpaces": true,
    // タブをスペースに変換

    "editor.detectIndentation": false
    // インデント自動検出を無効化（設定を優先）
}
```

#### ファイル設定

```json
{
    "files.trimTrailingWhitespace": true,
    // 行末の空白を削除

    "files.insertFinalNewline": true,
    // ファイル末尾に改行を挿入

    "files.trimFinalNewlines": true,
    // ファイル末尾の余分な改行を削除

    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        // エクスプローラーから除外するパターン
    }
}
```

#### Ruff設定

```json
{
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        // Pythonのフォーマッターとして Ruff を使用
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },

    "ruff.configurationPreference": "filesystemFirst",
    // pyproject.tomlの設定を優先

    "ruff.lint.run": "onSave",
    // リントの実行タイミング: "onSave", "onType"

    "ruff.organizeImports": true
    // インポート整理を有効化
}
```

#### テスト設定

```json
{
    "python.testing.pytestEnabled": true,
    // pytestを有効化

    "python.testing.unittestEnabled": false,
    // unittestを無効化（pytestと併用不可）

    "python.testing.pytestArgs": ["tests", "-v"]
    // pytestに渡す引数
}
```

#### ターミナル設定

```json
{
    "terminal.integrated.env.windows": {
        "PYTHONDONTWRITEBYTECODE": "1"
        // .pycファイルを生成しない
    }
}
```

---

### .vscode/extensions.json

チームに推奨する拡張機能の設定。

```json
{
    "recommendations": [
        "ms-python.python",          // Python基本サポート
        "ms-python.vscode-pylance",  // 高速な型チェック・補完
        "charliermarsh.ruff",        // リンター＆フォーマッター
        "ms-python.pytest-adapter",  // pytestサポート
        "eamodio.gitlens",           // Git履歴の可視化
        "mhutchie.git-graph",        // Gitグラフ表示
        "editorconfig.editorconfig", // EditorConfigサポート
        "tamasfe.even-better-toml",  // TOMLサポート
        "redhat.vscode-yaml",        // YAMLサポート
        "yzhang.markdown-all-in-one", // Markdownサポート
        "davidanson.vscode-markdownlint", // Markdownリンター
        "usernamehw.errorlens",      // エラーをインライン表示
        "gruntfuggly.todo-tree",     // TODO/FIXMEの可視化
        "streetsidesoftware.code-spell-checker" // スペルチェック
    ],
    "unwantedRecommendations": [
        "ms-python.black-formatter", // Ruffを使うため不要
        "ms-python.isort",           // Ruffを使うため不要
        "ms-python.flake8",          // Ruffを使うため不要
        "ms-python.pylint"           // Ruffを使うため不要
    ]
}
```

---

## テンプレートとしての使用方法

このプロジェクトをテンプレートとして新規プロジェクトを作成する際の変更箇所:

### 1. 必須の変更箇所

| ファイル | 変更箇所 | 説明 |
|---------|---------|------|
| `pyproject.toml` | `name` | パッケージ名 |
| `pyproject.toml` | `description` | プロジェクトの説明 |
| `pyproject.toml` | `authors` | 著者情報 |
| `pyproject.toml` | `keywords` | 検索キーワード |
| `pyproject.toml` | `packages` | ソースパッケージのパス |
| `tool.ruff.lint.isort` | `known-first-party` | プロジェクトのパッケージ名 |
| `tool.coverage.run` | `source` | カバレッジ対象パス |
| `src/study_python/` | ディレクトリ名 | パッケージ名に合わせてリネーム |

### 2. 必要に応じて変更

| 設定 | 変更理由の例 |
|-----|-------------|
| `requires-python` | 古いPython環境をサポートする場合 |
| `line-length` | チームの規約に合わせる（79, 100, 120など） |
| `tool.ruff.lint.select/ignore` | プロジェクトに合わせてルールを調整 |
| `tool.mypy.strict` | 型チェックの厳格度を調整 |
| `tool.coverage.report.fail_under` | 必要なカバレッジ率を調整 |

## ライセンス

MIT License
