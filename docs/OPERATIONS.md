# MindFlow 運用マニュアル

更新日: 2026-04-06

本ドキュメントは、MindFlowアプリケーションの運用に必要なすべての手順・知識を網羅する。新規開発者が本ドキュメントのみで運用を開始できることを目標とする。

---

## 目次

1. [インフラ構成](#1-インフラ構成)
2. [環境変数](#2-環境変数)
3. [ローカル開発](#3-ローカル開発)
4. [デプロイ](#4-デプロイ)
5. [CI/CD](#5-cicd)
6. [データベース](#6-データベース)
7. [認証・セキュリティ](#7-認証セキュリティ)
8. [テスト](#8-テスト)
9. [ログ・監視](#9-ログ監視)
10. [バージョン管理・リリース](#10-バージョン管理リリース)
11. [テキスト管理（ハードコーディング禁止）](#11-テキスト管理ハードコーディング禁止)
12. [開発ガイドライン](#12-開発ガイドライン)
13. [トラブルシューティング](#13-トラブルシューティング)
14. [スケーリング計画](#14-スケーリング計画)

---

## 1. インフラ構成

```
ユーザー
  ↓ HTTPS
┌─────────────────────────────┐
│  Render (Free Tier)         │
│  Docker / Python 3.12       │
│  FastAPI + Uvicorn          │
│  mindflow-gtd.onrender.com  │
└──────────┬──────────────────┘
           ↓ PostgreSQL (SSL)
┌─────────────────────────────┐
│  Neon (Free Tier)           │
│  PostgreSQL 17              │
│  Asia Pacific (Singapore)   │
│  Connection Pooling: ON     │
└─────────────────────────────┘
```

| サービス | 用途 | プラン | 月額 |
|---------|------|--------|------|
| Render | Webホスティング | Free | $0 |
| Neon | PostgreSQL DB | Free | $0 |
| GitHub Actions | CI/CD | Free | $0 |
| GitHub | ソースコード管理 | Free (Private) | $0 |

### 管理URL

| サービス | URL |
|---------|-----|
| Render ダッシュボード | https://dashboard.render.com |
| Neon ダッシュボード | https://console.neon.tech |
| GitHub リポジトリ | https://github.com/teppei19980914/mindflow |
| 本番アプリ | https://mindflow-gtd.onrender.com |

---

## 2. 環境変数

### 本番環境（Render）

| 変数名 | 設定方法 | 説明 |
|--------|---------|------|
| `SECRET_KEY` | Render自動生成 | セッション暗号化キー |
| `DATABASE_URL` | 手動設定（Neon接続文字列） | PostgreSQL接続URL |

### ローカル開発（run_local.bat内で自動設定）

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `SECRET_KEY` | `local-dev-secret-key` | 開発用固定キー |
| `DATABASE_URL` | `sqlite:///./mindflow_local.db` | ローカルSQLite |
| `DEBUG` | `true` | デバッグモード |

### CI環境（GitHub Actions内で自動設定）

| 変数名 | 値 |
|--------|-----|
| `SECRET_KEY` | `test-secret` |
| `DATABASE_URL` | `sqlite:///./test.db` |

---

## 3. ローカル開発

### 前提条件

- Python 3.12以上
- [uv](https://docs.astral.sh/uv/) インストール済み

### 起動手順

```
run_local.bat をダブルクリック
```

以下が自動実行される:
1. ポート8080の占有プロセスを自動kill
2. 依存関係インストール（`uv sync --extra dev`）
3. テスト実行（失敗時はサーバー起動しない）
4. `http://localhost:8080` でサーバー起動 + ブラウザ自動オープン

### 手動実行

```bash
# 依存関係インストール
uv sync --extra dev

# サーバー起動
SECRET_KEY=dev DATABASE_URL=sqlite:///./dev.db uv run mindflow-web

# テスト実行
uv run pytest tests/ -v

# リンター
uv run ruff check .

# フォーマッター
uv run ruff format .

# 型チェック
uv run mypy src/
```

### ディレクトリ構成

```
mindflow/
├── src/study_python/gtd/
│   ├── models.py                # データモデル
│   ├── repository_protocol.py   # リポジトリProtocol
│   ├── logic/                   # ビジネスロジック（Web非依存）
│   │   ├── collection.py        #   収集フェーズ
│   │   ├── clarification.py     #   明確化フェーズ
│   │   ├── organization.py      #   整理フェーズ
│   │   ├── execution.py         #   実行フェーズ
│   │   └── review.py            #   見直しフェーズ
│   └── web/                     # FastAPI Webアプリケーション
│       ├── app.py               #   アプリファクトリ + マイグレーション
│       ├── config.py            #   環境変数設定
│       ├── database.py          #   SQLAlchemy engine/session
│       ├── db_models.py         #   ORMモデル（User, GtdItem, Notification）
│       ├── db_repository.py     #   永続化リポジトリ（user_idフィルタ強制）
│       ├── auth.py              #   認証（bcrypt, バリデーション）
│       ├── labels.py            #   ラベル読み込みユーティリティ
│       ├── template_engine.py   #   共通Jinja2テンプレートエンジン
│       ├── dependencies.py      #   FastAPI DI（認証・リポジトリ注入）
│       ├── routers/             #   各フェーズのルーター
│       ├── templates/           #   Jinja2テンプレート + HTMXパーシャル
│       └── static/              #   CSS, JS, labels.json, releases.json
├── tests/                       # テストコード
├── docs/                        # ドキュメント
├── scripts/                     # ユーティリティスクリプト
├── logs/                        # ログファイル（.gitignore対象）
├── .github/workflows/ci.yml     # GitHub Actions
├── .claude/                     # Claude Code設定（hooks, skills, agents）
├── Dockerfile                   # Dockerイメージ定義
├── render.yaml                  # Renderデプロイ設定
├── run_local.bat                # ローカル開発起動スクリプト
├── pyproject.toml               # プロジェクト設定・依存関係
└── CLAUDE.md                    # 開発ガイドライン
```

---

## 4. デプロイ

### 自動デプロイ

```
git push origin main
  → GitHub Actions (CI: lint + format + test)
  → Render 自動デプロイ (Docker build + 起動)
```

### 手動デプロイ

Renderダッシュボード → mindflow-gtd → **Manual Deploy** → **Deploy latest commit**

### Dockerビルド

```dockerfile
FROM python:3.12-slim
# gcc + libpq-dev（bcrypt・PostgreSQL用）
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev
# uv パッケージマネージャ
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# ソースコピー + 依存関係インストール
COPY . .
RUN uv sync --no-dev --frozen
# 起動
CMD ["uv", "run", "uvicorn", "study_python.gtd.web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### デプロイ確認チェックリスト

- [ ] GitHub Actions CI が緑（全テストパス）
- [ ] Renderのデプロイステータスが「Live」
- [ ] ログインページが表示される（https://mindflow-gtd.onrender.com/login）
- [ ] 新規ユーザー登録ができる
- [ ] タスク登録→明確化→整理→実行の一連フローが動作する

---

## 5. CI/CD

### GitHub Actions ワークフロー

**ファイル**: `.github/workflows/ci.yml`

**トリガー**: `main`ブランチへのpush / PR

**実行内容**:

| ステップ | コマンド | 失敗時 |
|---------|---------|--------|
| Lint | `uv run ruff check .` | ルール違反があれば失敗 |
| Format | `uv run ruff format --check .` | フォーマット差分があれば失敗 |
| Test | `uv run pytest --cov=src/study_python --cov-report=term-missing -x` | テスト失敗 or カバレッジ75%未満で失敗 |

### Pre-commitフック

**ファイル**: `.pre-commit-config.yaml`

| フック | 内容 |
|--------|------|
| trailing-whitespace | 末尾空白除去 |
| end-of-file-fixer | ファイル末尾改行 |
| check-yaml/toml/json | 構文チェック |
| check-added-large-files | 1MB超のファイル追加を防止 |
| detect-private-key | 秘密鍵の混入を防止 |
| ruff (check + format) | リンター + フォーマッター |
| mypy | 型チェック |
| conventional-commits | コミットメッセージ規約 |

### コミットメッセージ規約

```
<type>(<scope>): <subject>

例:
feat(auth): ユーザー登録機能を追加
fix(db): PostgreSQL互換のマイグレーション修正
docs: README.mdを更新
```

**type**: feat, fix, docs, style, refactor, test, chore

---

## 6. データベース

### 本番DB（Neon PostgreSQL）

| 項目 | 値 |
|------|-----|
| サービス | Neon Free Tier |
| バージョン | PostgreSQL 17 |
| リージョン | Asia Pacific (Singapore) |
| ストレージ | 0.5 GB（無料枠） |
| 接続 | Connection Pooling ON, SSL必須 |
| 永続化 | 無期限（自動削除なし） |

### テーブル構成

| テーブル | 用途 | 主要カラム |
|---------|------|----------|
| `users` | ユーザー管理 | id, username, password_hash, created_at |
| `gtd_items` | タスク・プロジェクト | id, user_id, title, tag, status, importance, urgency, ... |
| `notifications` | 通知（リリース・実績） | id, user_id, notification_type, title, message, is_read |

### マイグレーション

新カラム追加時は`app.py`の`_migrate_add_project_planning_columns()`に追加する。アプリ起動時に自動実行され、既存カラムはスキップされる。

```python
new_columns = {
    "column_name": "TYPE DEFAULT value",
}
```

**注意**: PostgreSQLとSQLiteで互換性のあるSQL構文を使用すること（例: `BOOLEAN DEFAULT FALSE`、`BOOLEAN DEFAULT 0`はPostgreSQLでエラー）。

### バックアップ

- **Neon**: 自動日次バックアップ（Free Tierは6時間のリストアウィンドウ）
- **ローカル**: `mindflow_local.db`ファイルを手動コピー

---

## 7. 認証・セキュリティ

### 認証フロー

```
ユーザー登録 → bcryptハッシュ生成 → usersテーブルに保存
      ↓
ログイン → bcrypt照合 → セッションCookieにuser_id保存
      ↓
各リクエスト → require_auth() → user_id取得 → リポジトリにuser_id注入
      ↓
データアクセス → WHERE user_id = ? で自分のデータのみ返却
```

### セキュリティ対策一覧

| 脅威 | 対策 |
|------|------|
| パスワード漏洩 | bcryptハッシュ（ソルト自動生成） |
| データ漏洩（IDOR） | リポジトリ層でuser_idフィルタ強制 |
| タイミング攻撃 | 存在しないユーザーでもダミーハッシュ照合 |
| セッション固定 | ログイン時にsession.clear()で再生成 |
| ブルートフォース | IPベースレート制限（5回/5分） |
| XSS | CSPヘッダー + Jinja2自動エスケープ |
| クリックジャッキング | X-Frame-Options: DENY |
| CSRF | SameSite=lax Cookie |
| DB接続盗聴 | SSL必須（sslmode=require） |
| 秘密鍵混入 | pre-commitフック（detect-private-key） |

### パスワード要件

- ユーザー名: 英数字・アンダースコア・ハイフン、3〜50文字
- パスワード: 8文字以上

---

## 8. テスト

### 実行方法

```bash
# 全テスト
uv run pytest

# カバレッジ付き
uv run pytest --cov=src/study_python --cov-report=term-missing

# HTMLカバレッジレポート
uv run pytest --cov=src/study_python --cov-report=html
# → htmlcov/index.html をブラウザで開く

# 特定テストのみ
uv run pytest tests/gtd/logic/test_review.py -v

# 失敗時に即停止
uv run pytest -x
```

### テスト構成

| ディレクトリ | テスト対象 |
|------------|----------|
| `tests/gtd/logic/` | ビジネスロジック（収集・明確化・整理・実行・見直し） |
| `tests/gtd/logic/test_tenant_isolation.py` | クロステナントデータ分離（6パターン） |
| `tests/gtd/web/` | Webルーター（認証・ダッシュボード・Inbox・実行） |
| `tests/gtd/test_models.py` | データモデル |
| `tests/test_calculator.py` | ユーティリティ |
| `tests/test_logging_config.py` | ログ設定 |

### カバレッジ

- **閾値**: 75%（`pyproject.toml`の`fail_under`）
- **CI失敗条件**: カバレッジが75%を下回るとCIが失敗する
- **除外対象**: テストコード、`__pycache__`、`run.py`

---

## 9. ログ・監視

### ログ設定

| 項目 | 値 |
|------|-----|
| 出力先 | コンソール + `logs/`ディレクトリ |
| フォーマット | `{timestamp} \| {level} \| {module}:{function}:{line} \| {message}` |
| ローテーション | 10MB超で新ファイル、30世代保持 |
| レベル | 本番: INFO、開発: DEBUG |

### ログの確認方法

```bash
# 本番（Render）
Renderダッシュボード → Logs

# ローカル
logs/ ディレクトリのファイルを確認
```

### 監視項目

| 項目 | 確認方法 |
|------|---------|
| アプリ死活 | https://mindflow-gtd.onrender.com/login にアクセス |
| DB接続 | ログイン後にダッシュボードが表示されるか |
| CI状態 | GitHub Actions タブ |
| DB容量 | Neonダッシュボード → Storage |

---

## 10. バージョン管理・リリース

### リリース手順

**1. `releases.json`を編集**

```json
{
  "current_version": "1.1.0",
  "releases": [
    {
      "version": "1.1.0",
      "date": "2026-04-10",
      "title": "新機能リリース",
      "summary": "新機能を追加しました。",
      "changes": [
        "機能Aを追加",
        "機能Bを改善"
      ]
    },
    ...既存リリース
  ]
}
```

**2. コミット＆プッシュ**

```bash
git add src/study_python/gtd/web/static/releases.json
git commit -m "chore: v1.1.0 リリースノート追加"
git push origin main
```

**3. 自動で以下が反映される**

- 設定画面 → バージョン番号が更新
- アップデート情報ページ → 新バージョンが最上部に「最新」バッジ付きで表示
- 受信ボックス → 全ユーザーに通知が自動配信、未読バッジ表示

### 通知の自動配信の仕組み

```
releases.json にリリース追加
  ↓
ユーザーが受信ボックスを開く or ページロード時
  ↓
_sync_release_notifications() が自動実行
  ↓
未配信リリースの通知を notifications テーブルに INSERT
  ↓
未読バッジが表示される
```

---

## 11. テキスト管理（ハードコーディング禁止）

### ルール

**ユーザー向けテキスト（ページタイトル、ボタンラベル、エラーメッセージ、説明文等）をプログラムに直接記述してはならない。**

### 管理ファイル

- **`src/study_python/gtd/web/static/labels.json`** — 全テキストの一元管理

### 使い方

**テンプレートで:**

```html
{{ labels.nav.dashboard }}        → ダッシュボード
{{ labels.auth.error_credentials }} → ユーザー名またはパスワードが正しくありません
```

**Pythonで:**

```python
from study_python.gtd.web.labels import load_labels
labels = load_labels()
labels["auth"]["error_credentials"]
```

### テキスト追加・変更手順

1. `labels.json`に適切なセクション・キーを追加
2. テンプレートまたはPythonから`{{ labels.xxx }}`で参照
3. コード内にハードコードしない

### 対象外

- Pythonのdocstring（開発者向け）
- ログメッセージ（開発者向け）
- コメント（開発者向け）

---

## 12. 開発ガイドライン

### コーディング規約

- **PEP 8準拠**: ruffによる自動チェック
- **型ヒント必須**: 全関数にアノテーション
- **docstring**: Googleスタイル
- **命名**: 変数・関数=snake_case、クラス=PascalCase、定数=UPPER_SNAKE_CASE

### アーキテクチャ原則

```
Model (models.py) → Logic (logic/) → Web (web/)
```

- ロジック層はWeb層に依存しない
- `GtdRepositoryProtocol`でリポジトリを抽象化
- 全データアクセスは`user_id`でフィルタされたリポジトリ経由

### 新機能追加時のチェックリスト

- [ ] `labels.json`にテキストを追加（ハードコード禁止）
- [ ] テストを作成（カバレッジ75%以上を維持）
- [ ] `uv run ruff check .` が通る
- [ ] `uv run ruff format --check .` が通る
- [ ] `uv run pytest` が全件パス
- [ ] コミットメッセージがConventional Commits準拠

### Claude Code設定

| ディレクトリ | 用途 |
|------------|------|
| `.claude/hooks/` | 自動lint/format、危険コマンドブロック |
| `.claude/skills/` | カバレッジ方針、GUIテスト方針など |
| `.claude/agents/` | セキュリティレビュー、テスト生成、ドキュメント更新 |

---

## 13. トラブルシューティング

### デプロイ失敗

| 症状 | 原因 | 対処 |
|------|------|------|
| `Exited with status 1` | アプリ起動エラー | Renderログを確認。SECRET_KEYやDATABASE_URLの設定漏れが多い |
| `Exited with status 3` | DBマイグレーションエラー | PostgreSQL互換のSQL構文を使用しているか確認（`DEFAULT FALSE` not `DEFAULT 0`） |
| CI失敗 | lint/format/test不合格 | `uv run ruff check . --fix && uv run ruff format .`で修正 |
| Docker build失敗 | 依存関係エラー | `uv.lock`が最新か確認。`uv lock`で再生成 |

### アプリ不具合

| 症状 | 原因 | 対処 |
|------|------|------|
| ログインできない | DB接続エラー | Neonダッシュボードでステータス確認。接続文字列が正しいか確認 |
| 50秒の待ち時間 | Render Free Tierのコールドスタート | 仕様。有料プランで解消 |
| 他ユーザーのデータが見える | user_idフィルタの漏れ | `test_tenant_isolation.py`を実行して確認。リポジトリ層を点検 |
| テキストが表示されない | labels.jsonのキー不足 | ブラウザのソースを確認。`{{ labels.xxx }}`が空の場合はキーを追加 |

### ローカル開発

| 症状 | 原因 | 対処 |
|------|------|------|
| バッチが一瞬で閉じる | `uv`がPATHにない | コマンドプロンプトから手動実行してエラーを確認 |
| ポート競合 | 前回のプロセスが残存 | `run_local.bat`が自動killするが、残る場合はPC再起動 |
| DBロック | SQLiteファイルが別プロセスで使用中 | PC再起動。またはDB名を変えて起動 |

---

## 14. スケーリング計画

### 段階的スケーリング

```
Phase 1（現在）: $0/月 — ~50ユーザー
  Render Free + Neon Free

Phase 2: $7/月 — ~200ユーザー
  Render Starter（常時稼働、コールドスタート解消）

Phase 3: $26/月 — ~10,000ユーザー
  Render Starter + Neon Launch（10GB DB）

Phase 4: $50+/月 — 10,000ユーザー+
  Render Pro + Neon Scale + Redis + CDN
```

### スケーリング時の技術課題

| 課題 | 対策 | 着手タイミング |
|------|------|-------------|
| コールドスタート | 有料プラン or Keep-Alive ping | ユーザーからの苦情時 |
| 通知テーブル肥大化 | 既読90日超の自動削除バッチ | 1,000ユーザー超 |
| レート制限の分散 | Redis導入 | 複数インスタンス化時 |
| セッション共有 | Redis Session Store | 複数インスタンス化時 |
| 静的ファイル配信 | CDN導入（Cloudflare等） | 帯域問題発生時 |
| N+1クエリ | バッチクエリ最適化 | レスポンス劣化時 |
