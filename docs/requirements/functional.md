# MindFlow 要件定義書 - 機能要件

更新日: 2026-04-06

---

## 1. 概要

### 1.1 目的

本書は MindFlow Web アプリケーションの機能要件を定義する。
GTD 手法に基づくタスク管理の全フェーズを MECE に分類し、各要件を一意に識別可能な ID で管理する。

### 1.2 対象システム

| 項目 | 内容 |
|------|------|
| システム名 | MindFlow |
| 種別 | FastAPI + HTMX Web アプリケーション |
| アーキテクチャ | マルチテナント対応 |
| バックエンド | FastAPI (Python 3.12+) |
| フロントエンド | HTMX + Jinja2 テンプレート |
| データベース | PostgreSQL + SQLAlchemy |
| 対象ユーザー | 個人のタスク管理を行うユーザー |

### 1.3 要件分類体系

```
FR: 機能要件
├── FR-AUTH: 認証・認可
├── FR-COL: 収集フェーズ
├── FR-CLR: 明確化フェーズ
├── FR-ORG: 整理フェーズ
├── FR-EXE: 実行フェーズ
├── FR-REV: 見直しフェーズ
├── FR-DSH: ダッシュボード
├── FR-DAT: データ管理
├── FR-NAV: ナビゲーション・UI
├── FR-NOTIF: 通知システム
├── FR-ACHIEVE: 実績・マイルストーン
├── FR-PLAN: プロジェクト計画ウィザード
├── FR-SET: 設定ページ
├── FR-RELEASE: リリース管理
├── FR-ICONBAR: アイコンバー
└── FR-LABEL: テキスト外部化
```

---

## 2. FR-AUTH: 認証・認可要件

### FR-AUTH-001: ユーザー登録

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-AUTH-001 |
| 要件名 | ユーザー登録機能 |
| 説明 | 新規ユーザーが登録フォームでアカウント作成できること |
| エンドポイント | GET/POST /register |
| 入力 | ユーザー名（文字列、必須）、パスワード（文字列、必須）、パスワード確認（文字列、必須） |
| バリデーション | ユーザー名: 3〜20文字、英数字とアンダースコア、既存ユーザーとの重複確認。パスワード: 8文字以上、複雑さチェック |
| 出力 | User レコード作成、セッション自動設定、ダッシュボードにリダイレクト |
| セキュリティ | bcrypt によるパスワードハッシュ化（レート制限: 5 回/5 分） |
| 優先度 | 必須 |

### FR-AUTH-002: ユーザーログイン

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-AUTH-002 |
| 要件名 | ユーザーログイン機能 |
| 説明 | 登録済みユーザーがログインフォームで認証できること |
| エンドポイント | GET/POST /login |
| 入力 | ユーザー名（文字列）、パスワード（文字列） |
| 認証方式 | bcrypt によるパスワード検証 |
| 出力 | セッション作成、user_id と username をセッションに保存、ダッシュボードにリダイレクト |
| セキュリティ | レート制限: 5 回/5 分、IP アドレスベース |
| 優先度 | 必須 |

### FR-AUTH-003: ユーザーログアウト

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-AUTH-003 |
| 要件名 | ユーザーログアウト機能 |
| 説明 | ログイン中のユーザーがセッションを終了できること |
| エンドポイント | GET /logout |
| 処理 | セッション削除、ログインページにリダイレクト |
| 優先度 | 必須 |

### FR-AUTH-004: セッション管理

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-AUTH-004 |
| 要件名 | セッション管理とタイムアウト |
| 説明 | セッション情報を安全に管理し、タイムアウト処理を実行すること |
| セッション情報 | user_id, username を保存 |
| セキュリティ設定 | HttpOnly, Secure フラグ、SameSite=Lax |
| タイムアウト | 24 時間（86400秒） |
| 優先度 | 必須 |

### FR-AUTH-005: 認証要件チェック

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-AUTH-005 |
| 要件名 | エンドポイント認証要件の強制 |
| 説明 | 認証が必要なエンドポイントにアクセス時、認証されていない場合ログインページにリダイレクトすること |
| 依存関数 | require_auth() |
| スコープ | ダッシュボード以下の全ページ（/dashboard, /inbox, /clarification 等） |
| 優先度 | 必須 |

---

## 3. FR-COL: 収集フェーズ要件

### FR-COL-001: アイテム追加

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-COL-001 |
| 要件名 | Inbox へのアイテム追加 |
| 説明 | ユーザーがテキスト入力でタスクやアイデアを Inbox に登録できること |
| エンドポイント | GET /inbox, POST /api/inbox/add |
| 入力 | タイトル（文字列、必須） |
| 出力 | 新規 GtdItem（item_status=INBOX）を PostgreSQL に保存 |
| 制約 | タイトルが空白のみの場合は登録不可。前後空白はトリムする |
| 優先度 | 必須 |

### FR-COL-002: いつかやるリストへの移動

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-COL-002 |
| 要件名 | アイテムのいつかやるリストへの振り分け |
| 説明 | Inbox のアイテムを「いつかやる」リストに移動できること |
| エンドポイント | POST /api/inbox/{item_id}/to_someday |
| 処理 | item_status を SOMEDAY に変更、updated_at を更新、DB に保存 |
| 優先度 | 必須 |

### FR-COL-003: 参考資料への移動

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-COL-003 |
| 要件名 | アイテムの参考資料への振り分け |
| 説明 | Inbox のアイテムを「参考資料」に移動できること |
| エンドポイント | POST /api/inbox/{item_id}/to_reference |
| 処理 | item_status を REFERENCE に変更、updated_at を更新、DB に保存 |
| 優先度 | 必須 |

### FR-COL-004: アイテム削除

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-COL-004 |
| 要件名 | Inbox アイテムの削除 |
| 説明 | Inbox のアイテムを物理削除できること |
| エンドポイント | POST /inbox/{item_id}/delete |
| 処理 | 確認なしで物理削除、DB から削除 |
| 優先度 | 必須 |

### FR-COL-005: Inbox アイテム一覧表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-COL-005 |
| 要件名 | Inbox アイテムの一覧表示 |
| 説明 | 現在 Inbox にあるすべてのアイテムをカード形式で表示すること |
| エンドポイント | GET /inbox |
| テンプレート | inbox.html |
| 表示形式 | アイテムカード（タイトル、作成日時、アクションボタン） |
| 優先度 | 必須 |

---

## 4. FR-CLR: 明確化フェーズ要件

### FR-CLR-001: 決定木による分類

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-001 |
| 要件名 | GTD 決定木に基づくアイテム分類 |
| 説明 | SOMEDAY アイテムを 4 段階の質問（Yes/No）で分類できること |
| エンドポイント | GET /clarification, POST /api/clarification/* |
| 分類先 | 委任, カレンダー, プロジェクト, 即実行, タスク |
| 制約 | 決定木の順序は固定とする |
| 優先度 | 必須 |

### FR-CLR-002: 委任分類

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-002 |
| 要件名 | 委任タグの設定 |
| 説明 | 「自身が実施しなくてはいけないですか？」に No と回答した場合、tag=DELEGATION, status="not_started" を設定すること |
| エンドポイント | POST /api/clarification/{item_id}/classify_as_delegation |
| 優先度 | 必須 |

### FR-CLR-003: カレンダー分類

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-003 |
| 要件名 | カレンダータグの設定 |
| 説明 | 「日時が明確ですか？」に Yes と回答した場合、tag=CALENDAR, status="not_started" を設定すること |
| エンドポイント | POST /api/clarification/{item_id}/classify_as_calendar |
| 優先度 | 必須 |

### FR-CLR-004: プロジェクト分類

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-004 |
| 要件名 | プロジェクトタグの設定 |
| 説明 | 「2 ステップ以上のアクションが必要ですか？」に Yes と回答した場合、tag=PROJECT を設定すること |
| エンドポイント | POST /api/clarification/{item_id}/classify_as_project |
| 制約 | プロジェクトにはステータスを設定しない。整理フェーズの対象外とする |
| 優先度 | 必須 |

### FR-CLR-005: 即実行分類

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-005 |
| 要件名 | 即実行タグの設定 |
| 説明 | 「数分で実施できますか？」に Yes と回答した場合、tag=DO_NOW, status="not_started" を設定すること |
| エンドポイント | POST /api/clarification/{item_id}/classify_as_do_now |
| 優先度 | 必須 |

### FR-CLR-006: タスク分類とコンテキスト設定

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-006 |
| 要件名 | タスクタグとコンテキスト情報の設定 |
| 説明 | 「数分で実施できますか？」に No と回答した場合、コンテキスト入力フォームを表示し、tag=TASK + コンテキスト情報を設定すること |
| エンドポイント | POST /api/clarification/{item_id}/classify_as_task |
| 入力 | 実施場所（1 つ以上）、所要時間（1 つ）、エネルギーレベル（1 つ） |
| 優先度 | 必須 |

### FR-CLR-007: コンテキストデフォルト値

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-007 |
| 要件名 | コンテキスト入力のデフォルト値設定 |
| 説明 | コンテキスト入力フォームは常にデフォルト値で初期化されること |
| デフォルト | 実施場所=デスク、所要時間=30 分以内、エネルギー=中 |
| 制約 | タスク登録後もデフォルト値にリセットされること（クリアではない） |
| 優先度 | 必須 |

### FR-CLR-008: コンテキスト入力バリデーション

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-008 |
| 要件名 | コンテキスト入力の必須チェック |
| 説明 | 「タスクとして登録」ボタンクリック時に全項目の入力を検証すること |
| バリデーション | 実施場所: 1 つ以上選択、エネルギー: 1 つ選択 |
| エラー表示 | バリデーションエラー時は赤色メッセージを表示 |
| 視覚的表示 | 必須項目ラベルに赤色 `*` マークを表示 |
| 優先度 | 必須 |

### FR-CLR-009: 分類待ちアイテム一覧

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-009 |
| 要件名 | 分類待ちアイテムの順次処理 |
| 説明 | SOMEDAY かつ tag 未設定のアイテムを 1 件ずつ順番に処理すること |
| エンドポイント | GET /clarification |
| テンプレート | clarification.html |
| 表示 | 処理中アイテムのタイトル + 進捗（N / M 件） |
| 優先度 | 必須 |

---

## 5. FR-ORG: 整理フェーズ要件

### FR-ORG-001: 重要度・緊急度設定

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ORG-001 |
| 要件名 | アイテムへの重要度・緊急度スコア設定 |
| 説明 | タグ付け済み（PROJECT 以外）のアイテムに重要度と緊急度を設定できること |
| エンドポイント | POST /api/organization/{item_id}/set_importance_urgency |
| 入力 | 重要度（1-10）、緊急度（1-10） |
| 制約 | スライダーにより物理的に 1-10 の範囲に制限する |
| 優先度 | 必須 |

### FR-ORG-002: 4 象限マトリクス分類

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ORG-002 |
| 要件名 | アイテムの 4 象限マトリクスへの自動分類 |
| 説明 | 重要度と緊急度のスコアに基づき、4 象限（Q1-Q4）に自動分類すること |
| 分類基準 | 重要度 > 5 かつ緊急度 > 5 → Q1、重要度 > 5 → Q2、緊急度 > 5 → Q3、それ以外 → Q4 |
| 優先度 | 必須 |

### FR-ORG-003: マトリクスプレビュー

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ORG-003 |
| 要件名 | 整理画面でのマトリクスリアルタイムプレビュー |
| 説明 | スコア設定済みのアイテムをマトリクスビューで即座にプレビューできること |
| エンドポイント | GET /organization, POST /api/organization/* |
| テンプレート | organization.html |
| 更新 | HTMX による部分更新でリアルタイム反映 |
| 優先度 | 必須 |

### FR-ORG-004: 整理待ちアイテム一覧

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ORG-004 |
| 要件名 | 整理待ちアイテムの順次処理 |
| 説明 | needs_organization() == True のアイテムを 1 件ずつ順番に処理すること |
| エンドポイント | GET /organization |
| テンプレート | organization.html |
| 表示 | 処理中アイテムのタイトル + タグバッジ + 進捗（N / M 件） |
| 優先度 | 必須 |

---

## 6. FR-EXE: 実行フェーズ要件

### FR-EXE-001: アクティブタスク一覧表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-EXE-001 |
| 要件名 | 未完了タスクの一覧表示 |
| 説明 | tag 設定済みかつ PROJECT 以外の未完了タスクを一覧表示すること |
| エンドポイント | GET /execution |
| テンプレート | execution.html |
| ソート | 重要度降順 → 緊急度降順 |
| 優先度 | 必須 |

### FR-EXE-002: タグフィルタ

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-EXE-002 |
| 要件名 | タグによるタスクフィルタリング |
| 説明 | すべて / 依頼 / カレンダー / 即実行 / タスク でフィルタできること |
| エンドポイント | GET /execution?tag={tag} |
| テンプレート | execution.html + partials |
| 優先度 | 必須 |

### FR-EXE-003: ステータス変更

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-EXE-003 |
| 要件名 | タスクステータスの変更 |
| 説明 | 各タスクのステータスをコンボボックスで変更できること |
| エンドポイント | POST /api/execution/{item_id}/update_status |
| バリデーション | タグのステータス Enum に含まれる値のみ選択可能 |
| 優先度 | 必須 |

### FR-EXE-004: タグ別ステータス管理

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-EXE-004 |
| 要件名 | タグに応じたステータス選択肢の制御 |
| 説明 | タグごとに有効なステータス選択肢のみを表示すること |
| 詳細 | DELEGATION: 未着手/連絡待ち/完了、CALENDAR: 未着手/カレンダー登録済み、DO_NOW: 未着手/完了、TASK: 未着手/実施中/完了 |
| 優先度 | 必須 |

---

## 7. FR-REV: 見直しフェーズ要件

### FR-REV-001: 見直し対象一覧表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-REV-001 |
| 要件名 | 見直し対象アイテムの一覧表示 |
| 説明 | 完了タスク（is_done()==True）とプロジェクト（tag==PROJECT）を一覧表示すること |
| エンドポイント | GET /review |
| テンプレート | review.html |
| 表示 | 完了件数とプロジェクト件数を画面上部に表示 |
| 優先度 | 必須 |

### FR-REV-002: 完了タスクの Inbox 戻し

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-REV-002 |
| 要件名 | 完了タスクの Inbox への差し戻し |
| 説明 | 完了タスクの全属性（tag, status, locations, time_estimate, energy, importance, urgency）をリセットし、Inbox に戻せること |
| エンドポイント | POST /review/{item_id}/to_inbox |
| 処理 | item_status を INBOX に変更、その他属性をリセット、DB 保存 |
| 優先度 | 必須 |

### FR-REV-003: 見直しアイテム削除

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-REV-003 |
| 要件名 | 見直し対象アイテムの削除 |
| 説明 | 完了タスクまたはプロジェクトを物理削除できること |
| エンドポイント | POST /review/{item_id}/delete |
| 処理 | DB から削除 |
| 優先度 | 必須 |

### FR-REV-004: プロジェクト細分化

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-REV-004 |
| 要件名 | プロジェクトのサブタスクへの分解 |
| 説明 | プロジェクトを複数のサブタスクに分解し、各サブタスクを Inbox に登録後、元プロジェクトを削除できること |
| エンドポイント | POST /review/{item_id}/decompose |
| 入力 | サブタスクタイトル（1 件以上、最大 20 件） |
| 制約 | 空のタイトルは無視する。最低 1 件の有効なタイトルが必要 |
| 優先度 | 必須 |

### FR-REV-005: 空状態表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-REV-005 |
| 要件名 | 見直し対象がない場合の表示 |
| 説明 | 見直し対象アイテムが 0 件の場合、適切なメッセージを表示すること |
| エンドポイント | GET /review（アイテムなし） |
| テンプレート | review.html |
| 優先度 | 必須 |

---

## 8. FR-PLAN: プロジェクト計画ウィザード要件

プロジェクト管理に対して、ナチュラル・プランニング・モデルの 6 ステップに基づく計画ウィザードを提供する。

### FR-PLAN-001: ウィザード開始

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-PLAN-001 |
| 要件名 | プロジェクト計画ウィザードの起動 |
| 説明 | 見直しページから PROJECT タグのアイテムに対してウィザードを起動できること |
| エンドポイント | GET /review/{item_id}/plan?step=1 |
| テンプレート | partials/plan_step.html |
| 優先度 | 必須 |

### FR-PLAN-002: Step 1-2 目的と望ましい結果

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-PLAN-002 |
| 要件名 | ナチュラル・プランニング Step 1-2: 目的と望ましい結果の定義 |
| 説明 | ユーザーがプロジェクトの目的と望ましい結果を記入できること |
| エンドポイント | POST /review/{item_id}/plan/purpose |
| 入力 | purpose（テキスト）, outcome（テキスト） |
| 保存先 | GtdItem.project_purpose, GtdItem.project_outcome |
| 次ステップ | Step 3（ブレインストーミング） |
| 優先度 | 必須 |

### FR-PLAN-003: Step 3 ブレインストーミング

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-PLAN-003 |
| 要件名 | ナチュラル・プランニング Step 3: ブレインストーミング実施 |
| 説明 | ユーザーが思いつくタスク内容を複数行入力できること |
| エンドポイント | POST /review/{item_id}/plan/brainstorm |
| 入力 | brainstorm_items（複数行テキスト） |
| 処理 | 入力行を分割して brainstorm_items リストに変換 |
| 次ステップ | Step 4（整理） |
| 優先度 | 必須 |

### FR-PLAN-004: Step 4-5 整理と組織化

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-PLAN-004 |
| 要件名 | ナチュラル・プランニング Step 4-5: 整理と組織化 |
| 説明 | ブレインストーミング結果をウィザードが整理し、ユーザーが構造化・優先順位付けできること |
| エンドポイント | POST /review/{item_id}/plan/organize |
| 入力 | support_location（テキスト）, task_title[]（テキスト配列）, task_deadline[]（日付配列） |
| 保存先 | GtdItem.project_support_location |
| 次ステップ | Step 6（ネクストアクション） |
| 優先度 | 必須 |

### FR-PLAN-005: Step 6 ネクストアクション定義

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-PLAN-005 |
| 要件名 | ナチュラル・プランニング Step 6: ネクストアクションの確定 |
| 説明 | ユーザーがネクストアクションを選択し、サブタスクを生成できること |
| エンドポイント | POST /review/{item_id}/plan/execute |
| 入力 | task_title[]（テキスト配列）, task_deadline[]（日付配列）, next_action[]（チェックボックス配列） |
| 処理 | サブタスク作成（is_next_action フラグ設定）、元プロジェクトを削除 |
| 出力 | Inbox に複数のサブタスクを追加 |
| 優先度 | 必須 |

---

## 9. FR-DSH: ダッシュボード要件

### FR-DSH-001: サマリーカード表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DSH-001 |
| 要件名 | 数値サマリーの表示 |
| 説明 | Inbox 件数、アクティブタスク件数、完了件数、Q1（緊急×重要）件数を表示すること |
| エンドポイント | GET / |
| テンプレート | dashboard.html |
| 更新 | ページ表示時にリアルタイム計算 |
| 優先度 | 必須 |

### FR-DSH-002: マトリクスビュー表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DSH-002 |
| 要件名 | 重要度×緊急度マトリクスの表示 |
| 説明 | スコア設定済みの全アイテムを 4 象限マトリクスで表示すること |
| エンドポイント | GET / |
| テンプレート | dashboard.html + SVG レンダリング |
| 表示形式 | Canvas または SVG による 2D マトリクス |
| 優先度 | 必須 |

### FR-DSH-003: マトリクスの重複対策

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DSH-003 |
| 要件名 | 同一座標アイテムの視認性確保 |
| 説明 | 同じ重要度・緊急度のアイテムを Y 方向にオフセットして表示し、ラベルの重複を防ぐこと |
| 実装 | マトリクス計算ロジック（OrganizationLogic.get_matrix_quadrants()） |
| 優先度 | 必須 |

### FR-DSH-004: ガイダンス表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DSH-004 |
| 要件名 | GTD フロー案内メッセージ |
| 説明 | ユーザーの現在の状態に応じて、次にやるべきことをガイダンスメッセージで提示すること |
| メッセージ | Inbox → 明確化 → 整理 → 見直し → 実行 の フロー別ガイド |
| エンドポイント | GET / |
| テンプレート | dashboard.html |
| 優先度 | 必須 |

---

## 10. FR-DAT: データ管理要件

### FR-DAT-001: データ永続化

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DAT-001 |
| 要件名 | アプリケーションデータの永続化 |
| 説明 | すべてのアイテムデータを PostgreSQL に保存し、セッション継続時に復元できること |
| 保存先 | gtd_items テーブル（SQLAlchemy ORM） |
| 優先度 | 必須 |

### FR-DAT-002: マルチテナント対応

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DAT-002 |
| 要件名 | マルチテナント対応のデータ分離 |
| 説明 | ユーザーごとに独立したデータセットを保持し、他のユーザーのデータへのアクセスを防ぐこと |
| 実装 | GtdItem.user_id フィールドでフィルタリング |
| 優先度 | 必須 |

### FR-DAT-003: リポジトリパターン

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DAT-003 |
| 要件名 | リポジトリパターンによるデータアクセス |
| 説明 | DbGtdRepository クラスを通じてすべての DB アクセスを管理すること |
| 実装クラス | DbGtdRepository（study_python.gtd.web.db_repository） |
| 優先度 | 必須 |

### FR-DAT-004: トランザクション管理

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DAT-004 |
| 要件名 | データベーストランザクション管理 |
| 説明 | SQLAlchemy Session によるトランザクション一貫性を確保すること |
| 優先度 | 必須 |

---

## 11. FR-NOTIF: 通知システム要件

### FR-NOTIF-001: 通知データベース管理

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NOTIF-001 |
| 要件名 | 通知データの永続化 |
| 説明 | 全通知（システム、実績）を NotificationRow テーブルに保存すること |
| スキーマ | id, user_id, notification_type, title, message, is_read, created_at |
| 優先度 | 必須 |

### FR-NOTIF-002: リリース通知自動配信

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NOTIF-002 |
| 要件名 | リリースノート自動通知 |
| 説明 | releases.json に記載されたリリース情報を自動的に通知として配信すること |
| エンドポイント | GET /api/iconbar/notifications（同期時） |
| 処理 | _sync_release_notifications()で新規リリース検出、NotificationRow に追加 |
| 優先度 | 必須 |

### FR-NOTIF-003: 通知一覧表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NOTIF-003 |
| 要件名 | 受信箱（Inbox）での通知一覧表示 |
| 説明 | ユーザーが受信した全通知を時系列で表示できること |
| エンドポイント | GET /api/iconbar/notifications |
| テンプレート | partials/modal_inbox.html |
| ソート | created_at 降順 |
| 優先度 | 必須 |

### FR-NOTIF-004: 通知詳細表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NOTIF-004 |
| 要件名 | 通知詳細情報の表示 |
| 説明 | 通知をクリックして詳細情報を表示できること |
| エンドポイント | GET /api/iconbar/notifications/{notif_id} |
| テンプレート | partials/modal_inbox_detail.html |
| 優先度 | 必須 |

### FR-NOTIF-005: 通知既読管理

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NOTIF-005 |
| 要件名 | 通知の既読状態管理 |
| 説明 | ユーザーが通知を既読に変更できること |
| エンドポイント | GET /api/iconbar/notifications/{notif_id}（詳細表示時自動）、POST /api/iconbar/notifications/read_all |
| 処理 | is_read フラグを True に更新 |
| 優先度 | 必須 |

### FR-NOTIF-006: 未読バッジ表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NOTIF-006 |
| 要件名 | アイコンバーの未読通知バッジ |
| 説明 | 未読通知数をアイコンバーのベルアイコンにバッジで表示すること |
| エンドポイント | GET /api/iconbar/badge_count |
| テンプレート | HTML スニペット（`<span class="icon-badge">N</span>`） |
| バッジ形式 | 9+ で上限表示 |
| 優先度 | 必須 |

---

## 12. FR-ACHIEVE: 実績・マイルストーン要件

### FR-ACHIEVE-001: マイルストーン定義

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ACHIEVE-001 |
| 要件名 | タスク完成数による実績定義 |
| 説明 | 完成タスク+アクティブタスク数が特定の閾値に達したときマイルストーンを達成すること |
| 閾値 | 5, 10, 25, 50, 100, 250, 500 件 |
| 優先度 | 必須 |

### FR-ACHIEVE-002: 実績自動検出

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ACHIEVE-002 |
| 要件名 | マイルストーン自動検出と通知 |
| 説明 | ユーザーがアイコンバーの実績ボタンをクリックした時に、未通知の実績を検出して通知作成すること |
| エンドポイント | GET /api/iconbar/achievements |
| 処理 | 達成済みマイルストーン判定、新規 NotificationRow（achievement 型）作成 |
| 優先度 | 必須 |

### FR-ACHIEVE-003: 実績表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ACHIEVE-003 |
| 要件名 | 実績モーダルでの表示 |
| 説明 | ユーザーが達成した実績をモーダルウィンドウで一覧表示できること |
| エンドポイント | GET /api/iconbar/achievements |
| テンプレート | partials/modal_achievements.html |
| 表示項目 | 総タスク数、完成数、進行中数、達成バッジ一覧 |
| 優先度 | 必須 |

---

## 13. FR-SET: 設定ページ要件

### FR-SET-001: 設定ページ表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-SET-001 |
| 要件名 | 設定ページの表示 |
| 説明 | ユーザーが設定ページにアクセスできること |
| エンドポイント | GET /settings |
| テンプレート | settings.html |
| 優先度 | 必須 |

### FR-SET-002: アプリバージョン表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-SET-002 |
| 要件名 | アプリケーションバージョン表示 |
| 説明 | 現在使用しているアプリケーションのバージョンを表示すること |
| エンドポイント | GET /settings |
| データソース | releases.json の current_version フィールド |
| 優先度 | 必須 |

### FR-SET-003: アップデート情報表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-SET-003 |
| 要件名 | アップデート情報ページ |
| 説明 | 利用可能なすべてのリリース情報を表示できること |
| エンドポイント | GET /api/iconbar/releases |
| テンプレート | releases.html |
| 表示項目 | バージョン、リリース日、タイトル、サマリー |
| 優先度 | 必須 |

---

## 14. FR-RELEASE: リリース管理要件

### FR-RELEASE-001: リリースメタデータ

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-RELEASE-001 |
| 要件名 | リリース情報の管理 |
| 説明 | releases.json ファイルで all リリース情報を一元管理すること |
| ファイルパス | static/releases.json |
| スキーマ | { current_version, releases: [{ version, title, date, summary }] } |
| 優先度 | 必須 |

### FR-RELEASE-002: 現在バージョン管理

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-RELEASE-002 |
| 要件名 | 現在のアプリケーションバージョン |
| 説明 | releases.json の current_version フィールドで現在バージョンを管理すること |
| 用途 | 設定ページ、アップデート案内での表示 |
| 優先度 | 必須 |

---

## 15. FR-ICONBAR: アイコンバー要件

### FR-ICONBAR-001: ナビゲーション機能

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ICONBAR-001 |
| 要件名 | アイコンバーの各機能ボタン |
| 説明 | ユーザーが固定アイコンバーから各機能にアクセスできること |
| ボタン | チュートリアル, ヘルプ, 受信箱, お問い合わせ, 実績 |
| 実装 | JavaScript による HTMX モーダル表示 |
| 優先度 | 必須 |

### FR-ICONBAR-002: チュートリアルモーダル

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ICONBAR-002 |
| 要件名 | チュートリアルの表示 |
| 説明 | チュートリアルアイコンをクリックして、初期ユーザーガイドを表示できること |
| エンドポイント | - （スタティック表示） |
| テンプレート | 組み込みモーダル |
| 優先度 | 推奨 |

### FR-ICONBAR-003: ヘルプモーダル

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ICONBAR-003 |
| 要件名 | ヘルプの表示 |
| 説明 | ヘルプアイコンをクリックして、FAQ を表示できること |
| エンドポイント | - （スタティック表示） |
| テンプレート | 組み込みモーダル |
| 優先度 | 推奨 |

### FR-ICONBAR-004: 受信箱（通知）アイコン

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ICONBAR-004 |
| 要件名 | 受信箱機能へのアクセス |
| 説明 | 受信箱アイコンをクリックして通知一覧モーダルを表示できること |
| エンドポイント | GET /api/iconbar/notifications |
| テンプレート | partials/modal_inbox.html |
| バッジ | 未読通知数を表示 |
| 優先度 | 必須 |

### FR-ICONBAR-005: お問い合わせモーダル

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ICONBAR-005 |
| 要件名 | お問い合わせフォーム |
| 説明 | お問い合わせアイコンをクリックして、フィードバック送信フォームを表示できること |
| エンドポイント | GET /api/iconbar/contact |
| テンプレート | partials/modal_contact.html |
| 優先度 | 推奨 |

### FR-ICONBAR-006: 実績アイコン

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ICONBAR-006 |
| 要件名 | 実績表示へのアクセス |
| 説明 | 実績アイコンをクリックして、マイルストーン情報を表示できること |
| エンドポイント | GET /api/iconbar/achievements |
| テンプレート | partials/modal_achievements.html |
| 優先度 | 必須 |

---

## 16. FR-NAV: ナビゲーション・UI 要件

### FR-NAV-001: サイドバーナビゲーション

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NAV-001 |
| 要件名 | サイドバーによるページ切替 |
| 説明 | サイドバーのボタンクリックで Dashboard/Inbox/明確化/整理/実行/見直し の 6 ページを切替えられること |
| 実装 | Web サイドバー（ナビゲーションメニュー） |
| 制約 | 同時に 1 ページのみ表示（排他的選択） |
| 優先度 | 必須 |

### FR-NAV-002: バッジ表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NAV-002 |
| 要件名 | サイドバーボタンの件数バッジ表示 |
| 説明 | Inbox/明確化/整理/実行/見直し の各ボタンに対象アイテムの件数を表示すること |
| 更新 | HTMX による部分更新、データ変更時に自動更新 |
| 優先度 | 必須 |

### FR-NAV-003: ページ遷移

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NAV-003 |
| 要件名 | Web ページ遷移 |
| 説明 | リンククリックでページを遷移できること |
| 実装 | HTML リンク、必要に応じて HTMX |
| 優先度 | 必須 |

### FR-NAV-004: ダークテーマ

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NAV-004 |
| 要件名 | ダークテーマによるUI表示 |
| 説明 | Catppuccin Mocha ベースのダークテーマでアプリケーション全体を表示すること |
| 優先度 | 必須 |

### FR-NAV-005: 日本語表示名

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NAV-005 |
| 要件名 | タグ・ステータス等の日本語表示 |
| 説明 | タグ名、ステータス名、場所名、時間見積もり名、エネルギー名を日本語で表示すること |
| 実装 | labels.json からの読み込み |
| 優先度 | 必須 |

---

## 17. FR-LABEL: テキスト外部化要件

### FR-LABEL-001: ラベルJSON管理

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-LABEL-001 |
| 要件名 | ユーザー向けテキストの外部化 |
| 説明 | すべてのユーザー向けテキスト（ボタンラベル、メッセージ等）を labels.json で一元管理すること |
| ファイルパス | static/labels.json |
| 優先度 | 必須 |

### FR-LABEL-002: テキストハードコーディング禁止

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-LABEL-002 |
| 要件名 | ハードコーディング禁止ルール |
| 説明 | Python/Jinja2 テンプレート内に日本語テキストをハードコードしないこと |
| 実装 | load_labels()、get_label() 関数で取得 |
| 優先度 | 必須 |

### FR-LABEL-003: ラベル読み込みキャッシュ

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-LABEL-003 |
| 要件名 | ラベルのキャッシング |
| 説明 | ラベルの読み込みをキャッシュして、毎回の JSON パース処理を削減すること |
| 実装 | @lru_cache（maxsize=1） |
| 優先度 | 推奨 |

---

## 18. 要件トレーサビリティマトリクス

### 18.1 要件 → ルーター 対応表

| 要件 ID | ルーター | エンドポイント | テンプレート |
|---------|---------|-------------|-----------|
| FR-AUTH-001 | auth | POST /register | register.html |
| FR-AUTH-002 | auth | POST /login | login.html |
| FR-AUTH-003 | auth | GET /logout | - |
| FR-AUTH-004 | auth | SessionMiddleware | - |
| FR-AUTH-005 | dependencies | require_auth() | - |
| FR-COL-001 | inbox | POST /api/inbox/add | inbox.html |
| FR-COL-002 | inbox | POST /api/inbox/{id}/to_someday | item_list.html |
| FR-COL-003 | inbox | POST /api/inbox/{id}/to_reference | item_list.html |
| FR-COL-004 | inbox | POST /inbox/{id}/delete | item_list.html |
| FR-COL-005 | inbox | GET /inbox | inbox.html |
| FR-CLR-001 | clarification | GET /clarification | clarification.html |
| FR-CLR-002 | clarification | POST /api/clarification/{id}/classify_as_delegation | clarification.html |
| FR-CLR-003 | clarification | POST /api/clarification/{id}/classify_as_calendar | clarification.html |
| FR-CLR-004 | clarification | POST /api/clarification/{id}/classify_as_project | clarification.html |
| FR-CLR-005 | clarification | POST /api/clarification/{id}/classify_as_do_now | clarification.html |
| FR-CLR-006 | clarification | POST /api/clarification/{id}/classify_as_task | clarification.html |
| FR-CLR-009 | clarification | GET /clarification | clarification.html |
| FR-ORG-001 | organization | POST /api/organization/{id}/set_importance_urgency | organization.html |
| FR-ORG-002 | organization | GET /organization | organization.html |
| FR-ORG-003 | organization | GET /organization | organization.html |
| FR-ORG-004 | organization | GET /organization | organization.html |
| FR-EXE-001 | execution | GET /execution | execution.html |
| FR-EXE-002 | execution | GET /execution?tag= | execution.html |
| FR-EXE-003 | execution | POST /api/execution/{id}/update_status | execution.html |
| FR-EXE-004 | execution | POST /api/execution/{id}/update_status | execution.html |
| FR-REV-001 | review | GET /review | review.html |
| FR-REV-002 | review | POST /review/{id}/to_inbox | item_list.html |
| FR-REV-003 | review | POST /review/{id}/delete | item_list.html |
| FR-REV-004 | review | POST /review/{id}/decompose | item_list.html |
| FR-PLAN-001 | review | GET /review/{id}/plan | plan_step.html |
| FR-PLAN-002 | review | POST /review/{id}/plan/purpose | plan_step.html |
| FR-PLAN-003 | review | POST /review/{id}/plan/brainstorm | plan_step.html |
| FR-PLAN-004 | review | POST /review/{id}/plan/organize | plan_step.html |
| FR-PLAN-005 | review | POST /review/{id}/plan/execute | item_list.html |
| FR-DSH-001 | dashboard | GET / | dashboard.html |
| FR-DSH-002 | dashboard | GET / | dashboard.html |
| FR-DSH-004 | dashboard | GET / | dashboard.html |
| FR-NOTIF-002 | iconbar | GET /api/iconbar/notifications | modal_inbox.html |
| FR-NOTIF-003 | iconbar | GET /api/iconbar/notifications | modal_inbox.html |
| FR-NOTIF-004 | iconbar | GET /api/iconbar/notifications/{id} | modal_inbox_detail.html |
| FR-NOTIF-005 | iconbar | POST /api/iconbar/notifications/read_all | modal_inbox.html |
| FR-NOTIF-006 | iconbar | GET /api/iconbar/badge_count | HTML snippet |
| FR-ACHIEVE-002 | iconbar | GET /api/iconbar/achievements | modal_achievements.html |
| FR-ACHIEVE-003 | iconbar | GET /api/iconbar/achievements | modal_achievements.html |
| FR-SET-001 | settings_web | GET /settings | settings.html |
| FR-SET-002 | settings_web | GET /settings | settings.html |
| FR-RELEASE-001 | iconbar | - | releases.json |
| FR-ICONBAR-004 | iconbar | GET /api/iconbar/notifications | modal_inbox.html |
| FR-ICONBAR-005 | iconbar | GET /api/iconbar/contact | modal_contact.html |
| FR-ICONBAR-006 | iconbar | GET /api/iconbar/achievements | modal_achievements.html |
| FR-LABEL-001 | labels | - | labels.json |

### 18.2 要件 → テスト 対応表

| 要件 ID | テストファイル | テストケース |
|---------|-------------|------------|
| FR-AUTH-001 | test_auth.py | test_register_success, test_register_validation_*, test_register_rate_limit |
| FR-AUTH-002 | test_auth.py | test_login_success, test_login_invalid_credentials, test_login_rate_limit |
| FR-AUTH-003 | test_auth.py | test_logout |
| FR-COL-001 | test_collection.py | test_add_to_inbox, test_add_to_inbox_strips_whitespace, test_add_to_inbox_empty_raises |
| FR-COL-002 | test_collection.py | test_move_to_someday |
| FR-COL-003 | test_collection.py | test_move_to_reference |
| FR-COL-004 | test_collection.py | test_delete_item |
| FR-COL-005 | test_collection.py | test_get_inbox_items |
| FR-CLR-001 | test_clarification.py | test_clarification_decision_tree |
| FR-CLR-002 | test_clarification.py | test_classify_as_delegation |
| FR-CLR-003 | test_clarification.py | test_classify_as_calendar |
| FR-CLR-004 | test_clarification.py | test_classify_as_project |
| FR-CLR-005 | test_clarification.py | test_classify_as_do_now |
| FR-CLR-006 | test_clarification.py | test_classify_as_task_basic, test_classify_as_task_with_context |
| FR-CLR-008 | test_clarification.py | test_classify_as_task_validation |
| FR-CLR-009 | test_clarification.py | test_get_pending_items |
| FR-ORG-001 | test_organization.py | test_set_importance_urgency, test_*_validation |
| FR-ORG-002 | test_organization.py | test_get_matrix_quadrants |
| FR-ORG-004 | test_organization.py | test_get_unorganized_tasks |
| FR-EXE-001 | test_execution.py | test_get_active_tasks |
| FR-EXE-003 | test_execution.py | test_update_status_* |
| FR-EXE-004 | test_execution.py | test_get_available_statuses_* |
| FR-REV-001 | test_review.py | test_get_review_items_completed, test_get_review_items_project |
| FR-REV-002 | test_review.py | test_move_to_inbox |
| FR-REV-003 | test_review.py | test_delete_item |
| FR-REV-004 | test_review.py | test_decompose_project_success, test_decompose_project_* |
| FR-DAT-001 | test_db_repository.py | test_save_and_load, test_multitenancy |
| FR-NOTIF-001 | test_notification.py | test_notification_creation |
| FR-NOTIF-002 | test_notification.py | test_sync_release_notifications |
| FR-ACHIEVE-001 | test_achievement.py | test_milestone_thresholds |
| FR-ACHIEVE-002 | test_achievement.py | test_auto_detect_achievements |
| FR-LABEL-001 | test_labels.py | test_load_labels, test_get_label |

### 18.3 データモデル対応表

| 要件 ID | SQLAlchemy テーブル | ORM クラス |
|---------|------------------|---------|
| FR-AUTH-001~003 | users | User (db_models.py) |
| FR-COL-001~005 | gtd_items | GtdItem (models.py) |
| FR-CLR-001~009 | gtd_items | GtdItem (models.py) |
| FR-ORG-001~004 | gtd_items | GtdItem (models.py) |
| FR-EXE-001~004 | gtd_items | GtdItem (models.py) |
| FR-REV-001~005 | gtd_items | GtdItem (models.py) |
| FR-NOTIF-001~006 | notifications | NotificationRow (db_models.py) |
| FR-ACHIEVE-001~003 | notifications | NotificationRow (db_models.py) |

---

## 19. セキュリティ要件

### FR-SEC-001: パスワード暗号化

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-SEC-001 |
| 要件名 | bcrypt によるパスワード安全保管 |
| 説明 | ユーザーパスワードを平文で保存せず、bcrypt でハッシュ化して保存すること |
| 実装 | auth.register_user(), verify_credentials() |
| 優先度 | 必須 |

### FR-SEC-002: セッションセキュリティ

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-SEC-002 |
| 要件名 | セッション情報の安全な取り扱い |
| 説明 | セッションに HttpOnly, Secure, SameSite フラグを設定して XSS/CSRF 攻撃を防ぐこと |
| 実装 | SessionMiddleware 設定 |
| 優先度 | 必須 |

### FR-SEC-003: レート制限

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-SEC-003 |
| 要件名 | ログイン試行のレート制限 |
| 説明 | ブルートフォース攻撃を防ぐため、ログイン失敗回数に制限を設けること |
| 制限値 | 5 回/5 分（IP アドレスベース） |
| 実装 | auth.router の _is_rate_limited() |
| 優先度 | 必須 |

### FR-SEC-004: CSRF 対策

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-SEC-004 |
| 要件名 | CSRF トークン検証 |
| 説明 | POST リクエストに CSRF 保護を実装すること |
| 優先度 | 推奨 |

### FR-SEC-005: Content Security Policy

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-SEC-005 |
| 要件名 | HTTP セキュリティヘッダーの設定 |
| 説明 | X-Content-Type-Options, X-Frame-Options, CSP ヘッダーを設定して XSS/clickjacking 攻撃を防ぐこと |
| 実装 | app.py security_headers_middleware |
| 優先度 | 必須 |

---

## 20. パフォーマンス要件

### FR-PERF-001: ラベルキャッシング

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-PERF-001 |
| 要件名 | labels.json の読み込みキャッシング |
| 説明 | labels.json の読み込みをキャッシュして毎回のパース処理を削減すること |
| 実装 | @lru_cache(maxsize=1) |
| 優先度 | 推奨 |

### FR-PERF-002: データベースインデックス

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-PERF-002 |
| 要件名 | DB クエリの最適化 |
| 説明 | user_id カラムにインデックスを設定してマルチテナント検索を高速化すること |
| 優先度 | 推奨 |

---

## 21. 要件の更新履歴

| 日時 | 変更内容 |
|------|---------|
| 2026-04-06 | 新規作成。PySide6 デスクトップアプリケーションから FastAPI + HTMX Web アプリケーションへの大規模リライト。FR-AUTH, FR-NOTIF, FR-ACHIEVE, FR-PLAN, FR-SET, FR-RELEASE, FR-ICONBAR, FR-LABEL 要件セクションを新規追加。FR-DAT は PostgreSQL + SQLAlchemy に更新。FR-NAV はサイドバー Web UI に変更。トレーサビリティマトリクスはルーター・テンプレート・DB スキーマベースに更新。 |
