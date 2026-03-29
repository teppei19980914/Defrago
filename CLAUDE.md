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
├── docs/               # ドキュメント
├── scripts/            # ユーティリティスクリプト
└── logs/               # ログファイル（.gitignore対象）
```

## コーディング規約

### Python スタイルガイド

- **PEP 8 準拠**: ruffによる自動フォーマット・リント
- **型ヒント必須**: すべての関数に型アノテーションを付与
- **docstring**: Google スタイルを使用

### 命名規則

- **変数・関数**: snake_case
- **クラス**: PascalCase
- **定数**: UPPER_SNAKE_CASE
- **プライベート**: 先頭にアンダースコア

### インポート順序

1. 標準ライブラリ → 2. サードパーティ → 3. ローカルモジュール

## 開発コマンド

```bash
uv sync                    # 依存関係インストール
uv run ruff check .        # リンター
uv run ruff format .       # フォーマッター
uv run mypy src/           # 型チェック
uv run pytest              # テスト
uv run pytest --cov=src/study_python --cov-report=html  # カバレッジ付き
```

## コミットメッセージ規約

[Conventional Commits](https://www.conventionalcommits.org/) に従う：
`<type>(<scope>): <subject>`

Type: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## テスト方針

- 各関数・メソッドにユニットテストを作成
- 命名: `test_<関数名>_<テスト条件>`
- 配置: `tests/` に `test_*.py` として配置
- 共通セットアップは `conftest.py` に定義
- **コード変更後は必ず `uv run pytest` を実行**
- テスト失敗時は自動で原因調査・修正を行う（詳細: `/test-autofix`）
- カバレッジ100%を目指す（詳細: `/coverage`）
- GUIテストは GUI/ロジック分離が必須（詳細: `/gui-test`）

## エラーハンドリング

- 汎用 `Exception` ではなく具体的な例外を使用
- 必要に応じてドメイン固有のカスタム例外を定義
- エラー時は適切なログレベルで記録（詳細: `/logging`）

## セキュリティ注意事項

- 機密情報はコードにハードコードしない（環境変数 or `.env`）
- ユーザー入力は必ずバリデーション・サニタイズ

## リリース前チェック（必須）

コミット前に セキュリティ・パフォーマンス・テスト の3チェックを実施（詳細: `/release-check`）

## ドキュメント管理

プログラム変更時は関連ドキュメントを最新化すること（詳細: `/doc-update`）

## ClaudeCode 使用時の注意

1. **変更前に確認**: ファイルを編集する前に必ず内容を確認する
2. **小さな変更**: 大きな変更は小さなステップに分割する
3. **テスト実行**: コード変更後は必ずテストを実行する
4. **既存コードの尊重**: プロジェクトの既存パターンに従う
