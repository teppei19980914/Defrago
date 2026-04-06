# MindFlow インフラ構成・コスト分析

更新日: 2026-04-06

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

### 構成要素

| コンポーネント | サービス | プラン | 用途 |
|--------------|---------|--------|------|
| Webサーバー | Render | Free | FastAPI アプリケーションホスティング |
| データベース | Neon | Free | PostgreSQL 17（ユーザー・タスク・通知） |
| CI/CD | GitHub Actions | Free | lint / format / テスト自動実行 |
| ソースコード | GitHub | Free (Private) | バージョン管理 |
| ドメイン | Render提供 | 無料 | mindflow-gtd.onrender.com |

### 技術スタック

| カテゴリ | 技術 |
|---------|------|
| 言語 | Python 3.12 |
| Webフレームワーク | FastAPI + Jinja2 + HTMX |
| ORM | SQLAlchemy 2.0 |
| DB | PostgreSQL 17 (Neon) / SQLite (ローカル開発) |
| 認証 | bcrypt + セッションCookie |
| コンテナ | Docker (python:3.12-slim) |
| テスト | pytest + httpx |
| リンター | ruff |
| 型チェック | mypy (strict) |

## 2. 各サービスの無料枠

### Render Free Tier

| リソース | 上限 | MindFlow使用量 |
|---------|------|---------------|
| インスタンス | 1台 | 1台 |
| 帯域 | 100 GB/月 | 静的108KB × PV数 |
| ビルド時間 | 500分/月 | 約5分/デプロイ |
| 稼働時間 | 750時間/月 | 24h × 31日 = 744h |

**制約**: 15分無通信でスリープ → 再アクセス時に約50秒のコールドスタート

### Neon Free Tier

| リソース | 上限 | MindFlow使用量 |
|---------|------|---------------|
| ストレージ | 0.5 GB | 1,000ユーザーで約50MB |
| Compute | 月400時間 | 常時稼働で十分 |
| 転送量 | 5 GB/月 | 通常到達しない |
| プロジェクト | 100 | 1 |
| ブランチ | 10/プロジェクト | 1 (production) |

**永続化**: 無期限（Supabase Free Tierのような90日削除制限なし）

### GitHub Actions Free Tier

| リソース | 上限 | MindFlow使用量 |
|---------|------|---------------|
| 実行時間 | 2,000分/月 (Private) | 約3分/回 × push回数 |
| ストレージ | 500 MB | 問題なし |

## 3. コスト分析

### 現在のコスト: $0/月

全サービスが無料枠内で運用可能。

### コスト発生シナリオ

| ユーザー数 | 推定コスト | ボトルネック | 必要な対応 |
|-----------|-----------|------------|----------|
| 1-50人 | **$0/月** | コールドスタート50秒 | 現状のまま |
| 50-200人 | $7/月 | 同時接続・レスポンス | Render Starter Plan |
| 200-1,000人 | $14-25/月 | DB接続数・帯域 | Starter + CDN |
| 1,000人+ | $25-50+/月 | 水平スケーリング | Pro Plan + Redis |

### データベース成長予測

| ユーザー数 | gtd_items | notifications | 合計推定サイズ |
|-----------|-----------|---------------|-------------|
| 10人 | 1,000行 | 100行 | ~1 MB |
| 100人 | 10,000行 | 1,000行 | ~10 MB |
| 1,000人 | 100,000行 | 10,000行 | ~100 MB |
| 10,000人 | 1,000,000行 | 100,000行 | ~500 MB (上限に近い) |

**Neon Free上限 0.5GB到達**: 約10,000ユーザー（Neon Launchプランへの移行: $19/月）

## 4. セキュリティ構成

| 項目 | 実装 |
|------|------|
| パスワード保存 | bcrypt (ソルト自動生成) |
| セッション | 署名Cookie (SameSite=lax, HTTPS-only) |
| データ分離 | リポジトリ層でuser_idフィルタを強制 |
| DB接続 | SSL必須 (sslmode=require) |
| レート制限 | IPベース 5回/5分 (ログイン・登録) |
| HTTPヘッダー | CSP, X-Frame-Options, HSTS, Referrer-Policy |
| 入力バリデーション | ユーザー名: 正規表現, パスワード: 8文字以上 |

## 5. 既知の制約と改善計画

### 現在の制約

| 制約 | 影響 | 優先度 |
|------|------|--------|
| コールドスタート50秒 | 初回アクセスのUX低下 | 中 |
| 通知テーブルにretention policyなし | 長期的なDB肥大化 | 低 |
| レート制限がインメモリ | 複数インスタンス時に無効 | 低（現在1インスタンス） |
| CDN未導入 | 静的ファイル配信が非効率 | 低（108KBで軽量） |

### スケーリングロードマップ

```
Phase 1 (現在): $0/月
  Render Free + Neon Free
  対象: ~50ユーザー

Phase 2: $7/月
  Render Starter (常時稼働)
  対象: ~200ユーザー

Phase 3: $26/月
  Render Starter + Neon Launch
  対象: ~10,000ユーザー

Phase 4: $50+/月
  Render Pro + Neon Scale + Redis + CDN
  対象: 10,000ユーザー+
```

## 6. 運用手順

### デプロイ

```bash
git push origin main
# → GitHub Actions (CI) → Render 自動デプロイ
```

### 環境変数 (Render)

| 変数 | 設定場所 | 用途 |
|------|---------|------|
| SECRET_KEY | Render (自動生成) | セッション暗号化 |
| DATABASE_URL | Render (Neon接続文字列) | PostgreSQL接続 |

### ローカル開発

```bash
run_local.bat  # ポート8080、SQLite使用
```

### バージョンリリース

```
releases.json を編集 → git push
→ 設定画面・アップデート情報・受信ボックスに自動反映
```

## 7. 変更履歴

| 日付 | 変更内容 |
|------|---------|
| 2026-04-06 | Supabase → Neon Free PostgreSQLに移行 |
| 2026-04-05 | マルチテナント化（ユーザー登録・データ分離） |
| 2026-04-05 | アイコンバー・通知・実績・設定画面追加 |
| 2026-04-05 | ハードコーディング排除（labels.json外部化） |
