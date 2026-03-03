# MindFlow 要件定義書 - 機能要件

更新日: 2026-03-03

---

## 1. 概要

### 1.1 目的

本書は MindFlow アプリケーションの機能要件を定義する。
GTD 手法に基づくタスク管理の全フェーズを MECE に分類し、各要件を一意に識別可能な ID で管理する。

### 1.2 対象システム

| 項目 | 内容 |
|------|------|
| システム名 | MindFlow |
| 種別 | デスクトップ GUI アプリケーション |
| 対象ユーザー | 個人のタスク管理を行うユーザー |

### 1.3 要件分類体系

```
FR: 機能要件
├── FR-COL: 収集フェーズ
├── FR-CLR: 明確化フェーズ
├── FR-ORG: 整理フェーズ
├── FR-EXE: 実行フェーズ
├── FR-REV: 見直しフェーズ
├── FR-DSH: ダッシュボード
├── FR-DAT: データ管理
└── FR-NAV: ナビゲーション・UI
```

---

## 2. FR-COL: 収集フェーズ要件

### FR-COL-001: アイテム追加

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-COL-001 |
| 要件名 | Inbox へのアイテム追加 |
| 説明 | ユーザーがテキスト入力でタスクやアイデアを Inbox に登録できること |
| 入力 | タイトル（文字列、必須） |
| 出力 | 新規 GtdItem（item_status=INBOX） |
| 制約 | タイトルが空白のみの場合は登録不可。前後空白はトリムする |
| 優先度 | 必須 |

### FR-COL-002: いつかやるリストへの移動

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-COL-002 |
| 要件名 | アイテムのいつかやるリストへの振り分け |
| 説明 | Inbox のアイテムを「いつかやる」リストに移動できること |
| 処理 | item_status を SOMEDAY に変更 |
| 優先度 | 必須 |

### FR-COL-003: 参考資料への移動

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-COL-003 |
| 要件名 | アイテムの参考資料への振り分け |
| 説明 | Inbox のアイテムを「参考資料」に移動できること |
| 処理 | item_status を REFERENCE に変更 |
| 優先度 | 必須 |

### FR-COL-004: アイテム削除

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-COL-004 |
| 要件名 | Inbox アイテムの削除 |
| 説明 | Inbox のアイテムを確認ダイアログ付きで物理削除できること |
| 制約 | 削除前に確認ダイアログを表示すること |
| 優先度 | 必須 |

### FR-COL-005: Inbox アイテム一覧表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-COL-005 |
| 要件名 | Inbox アイテムの一覧表示 |
| 説明 | 現在 Inbox にあるすべてのアイテムをカード形式で表示すること |
| 優先度 | 必須 |

---

## 3. FR-CLR: 明確化フェーズ要件

### FR-CLR-001: 決定木による分類

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-001 |
| 要件名 | GTD 決定木に基づくアイテム分類 |
| 説明 | SOMEDAY アイテムを 4 段階の質問（Yes/No）で分類できること |
| 分類先 | 委任, カレンダー, プロジェクト, 即実行, タスク |
| 制約 | 決定木の順序は固定とする |
| 優先度 | 必須 |

### FR-CLR-002: 委任分類

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-002 |
| 要件名 | 委任タグの設定 |
| 説明 | 「自身が実施しなくてはいけないですか？」に No と回答した場合、tag=DELEGATION, status="not_started" を設定すること |
| 優先度 | 必須 |

### FR-CLR-003: カレンダー分類

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-003 |
| 要件名 | カレンダータグの設定 |
| 説明 | 「日時が明確ですか？」に Yes と回答した場合、tag=CALENDAR, status="not_started" を設定すること |
| 優先度 | 必須 |

### FR-CLR-004: プロジェクト分類

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-004 |
| 要件名 | プロジェクトタグの設定 |
| 説明 | 「2 ステップ以上のアクションが必要ですか？」に Yes と回答した場合、tag=PROJECT を設定すること |
| 制約 | プロジェクトにはステータスを設定しない。整理フェーズの対象外とする |
| 優先度 | 必須 |

### FR-CLR-005: 即実行分類

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-005 |
| 要件名 | 即実行タグの設定 |
| 説明 | 「数分で実施できますか？」に Yes と回答した場合、tag=DO_NOW, status="not_started" を設定すること |
| 優先度 | 必須 |

### FR-CLR-006: タスク分類とコンテキスト設定

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-CLR-006 |
| 要件名 | タスクタグとコンテキスト情報の設定 |
| 説明 | 「数分で実施できますか？」に No と回答した場合、コンテキスト入力フォームを表示し、tag=TASK + コンテキスト情報を設定すること |
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
| 表示 | 処理中アイテムのタイトル + 進捗（N / M 件） |
| 優先度 | 必須 |

---

## 4. FR-ORG: 整理フェーズ要件

### FR-ORG-001: 重要度・緊急度設定

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ORG-001 |
| 要件名 | アイテムへの重要度・緊急度スコア設定 |
| 説明 | タグ付け済み（PROJECT 以外）のアイテムに重要度と緊急度を設定できること |
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
| 更新 | アイテム評価後にリアルタイムで反映 |
| 優先度 | 必須 |

### FR-ORG-004: 整理待ちアイテム一覧

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-ORG-004 |
| 要件名 | 整理待ちアイテムの順次処理 |
| 説明 | needs_organization() == True のアイテムを 1 件ずつ順番に処理すること |
| 表示 | 処理中アイテムのタイトル + タグバッジ + 進捗（N / M 件） |
| 優先度 | 必須 |

---

## 5. FR-EXE: 実行フェーズ要件

### FR-EXE-001: アクティブタスク一覧表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-EXE-001 |
| 要件名 | 未完了タスクの一覧表示 |
| 説明 | tag 設定済みかつ PROJECT 以外の未完了タスクを一覧表示すること |
| ソート | 重要度降順 → 緊急度降順 |
| 優先度 | 必須 |

### FR-EXE-002: タグフィルタ

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-EXE-002 |
| 要件名 | タグによるタスクフィルタリング |
| 説明 | すべて / 依頼 / カレンダー / 即実行 / タスク でフィルタできること |
| 優先度 | 必須 |

### FR-EXE-003: ステータス変更

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-EXE-003 |
| 要件名 | タスクステータスの変更 |
| 説明 | 各タスクのステータスをコンボボックスで変更できること |
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

## 6. FR-REV: 見直しフェーズ要件

### FR-REV-001: 見直し対象一覧表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-REV-001 |
| 要件名 | 見直し対象アイテムの一覧表示 |
| 説明 | 完了タスク（is_done()==True）とプロジェクト（tag==PROJECT）を一覧表示すること |
| 表示 | 完了件数とプロジェクト件数を画面上部に表示 |
| 優先度 | 必須 |

### FR-REV-002: 完了タスクの Inbox 戻し

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-REV-002 |
| 要件名 | 完了タスクの Inbox への差し戻し |
| 説明 | 完了タスクの全属性（tag, status, locations, time_estimate, energy, importance, urgency）をリセットし、Inbox に戻せること |
| 優先度 | 必須 |

### FR-REV-003: 見直しアイテム削除

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-REV-003 |
| 要件名 | 見直し対象アイテムの削除 |
| 説明 | 完了タスクまたはプロジェクトを確認ダイアログ付きで物理削除できること |
| 優先度 | 必須 |

### FR-REV-004: プロジェクト細分化

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-REV-004 |
| 要件名 | プロジェクトのサブタスクへの分解 |
| 説明 | プロジェクトを複数のサブタスクに分解し、各サブタスクを Inbox に登録後、元プロジェクトを削除できること |
| 入力 | サブタスクタイトル（1 件以上、最大 20 件） |
| 制約 | 空のタイトルは無視する。最低 1 件の有効なタイトルが必要 |
| 優先度 | 必須 |

### FR-REV-005: 空状態表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-REV-005 |
| 要件名 | 見直し対象がない場合の表示 |
| 説明 | 見直し対象アイテムが 0 件の場合、適切なメッセージを表示すること |
| 優先度 | 必須 |

---

## 7. FR-DSH: ダッシュボード要件

### FR-DSH-001: サマリーカード表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DSH-001 |
| 要件名 | 数値サマリーの表示 |
| 説明 | Inbox 件数、アクティブタスク件数、完了件数、Q1（緊急×重要）件数を表示すること |
| 更新 | 画面表示時にリアルタイム計算 |
| 優先度 | 必須 |

### FR-DSH-002: マトリクスビュー表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DSH-002 |
| 要件名 | 重要度×緊急度マトリクスの表示 |
| 説明 | スコア設定済みの全アイテムを 4 象限マトリクスで表示すること |
| 優先度 | 必須 |

### FR-DSH-003: マトリクスの重複対策

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DSH-003 |
| 要件名 | 同一座標アイテムの視認性確保 |
| 説明 | 同じ重要度・緊急度のアイテムを Y 方向にオフセットして表示し、ラベルの重複を防ぐこと |
| 優先度 | 必須 |

### FR-DSH-004: マトリクスのツールチップ

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DSH-004 |
| 要件名 | マトリクスドット/ラベルのツールチップ表示 |
| 説明 | ドットまたはラベルテキスト上にマウスホバーした際、タイトル・重要度・緊急度をツールチップで表示すること |
| 優先度 | 必須 |

---

## 8. FR-DAT: データ管理要件

### FR-DAT-001: データ永続化

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DAT-001 |
| 要件名 | アプリケーションデータの永続化 |
| 説明 | すべてのアイテムデータを JSON ファイルに保存し、次回起動時に復元できること |
| 保存先 | ~/.mindflow/gtd_data.json |
| 優先度 | 必須 |

### FR-DAT-002: 即時保存

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DAT-002 |
| 要件名 | データ変更時の即時保存 |
| 説明 | ユーザー操作によりデータが変更された際、即座にファイルに保存すること |
| 優先度 | 必須 |

### FR-DAT-003: 破損データ耐性

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DAT-003 |
| 要件名 | データファイル破損時の耐性 |
| 説明 | JSON ファイルが破損している場合、エラーログを出力し空の状態で起動すること（クラッシュしない） |
| 優先度 | 必須 |

### FR-DAT-004: ディレクトリ自動作成

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-DAT-004 |
| 要件名 | データ保存ディレクトリの自動作成 |
| 説明 | ~/.mindflow/ ディレクトリが存在しない場合、自動的に作成すること |
| 優先度 | 必須 |

---

## 9. FR-NAV: ナビゲーション・UI 要件

### FR-NAV-001: サイドバーナビゲーション

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NAV-001 |
| 要件名 | サイドバーによるページ切替 |
| 説明 | サイドバーのボタンクリックで Dashboard/Inbox/明確化/整理/実行/見直し の 6 ページを切替えられること |
| 制約 | 同時に 1 ページのみ表示（排他的選択） |
| 優先度 | 必須 |

### FR-NAV-002: バッジ表示

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NAV-002 |
| 要件名 | サイドバーボタンの件数バッジ表示 |
| 説明 | Inbox/明確化/整理/実行/見直し の各ボタンに対象アイテムの件数を表示すること |
| 更新 | データ変更時に自動更新 |
| 優先度 | 必須 |

### FR-NAV-003: ステータスバー

| 項目 | 内容 |
|------|------|
| 要件 ID | FR-NAV-003 |
| 要件名 | ステータスバーによる全体統計表示 |
| 説明 | 全件数・タスク件数・完了件数をウィンドウ下部に常時表示すること |
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
| 優先度 | 必須 |

---

## 10. 要件トレーサビリティマトリクス

### 10.1 要件 → 設計 → 実装 対応表

| 要件 ID | 設計コンポーネント | ロジック | GUI |
|---------|-----------------|---------|-----|
| FR-COL-001 | CollectionLogic | add_to_inbox() | InboxWidget |
| FR-COL-002 | CollectionLogic | move_to_someday() | InboxWidget |
| FR-COL-003 | CollectionLogic | move_to_reference() | InboxWidget |
| FR-COL-004 | CollectionLogic | delete_item() | InboxWidget + ConfirmDialog |
| FR-COL-005 | CollectionLogic | get_inbox_items() | InboxWidget |
| FR-CLR-001 | ClarificationLogic | classify_as_*() | ClarificationWidget |
| FR-CLR-002 | ClarificationLogic | classify_as_delegation() | ClarificationWidget Step 0 |
| FR-CLR-003 | ClarificationLogic | classify_as_calendar() | ClarificationWidget Step 1 |
| FR-CLR-004 | ClarificationLogic | classify_as_project() | ClarificationWidget Step 2 |
| FR-CLR-005 | ClarificationLogic | classify_as_do_now() | ClarificationWidget Step 3 |
| FR-CLR-006 | ClarificationLogic | classify_as_task() | ClarificationWidget Context Form |
| FR-CLR-007 | ClarificationWidget | _reset_context_defaults() | ClarificationWidget |
| FR-CLR-008 | ClarificationLogic + Widget | validate_input + _validate_context() | ClarificationWidget |
| FR-CLR-009 | ClarificationLogic | get_pending_items() | ClarificationWidget |
| FR-ORG-001 | OrganizationLogic | set_importance_urgency() | OrganizationWidget |
| FR-ORG-002 | OrganizationLogic | get_matrix_quadrants() | OrganizationWidget |
| FR-ORG-003 | MatrixView | set_items() / paintEvent() | OrganizationWidget |
| FR-ORG-004 | OrganizationLogic | get_unorganized_tasks() | OrganizationWidget |
| FR-EXE-001 | ExecutionLogic | get_active_tasks() | TaskListWidget |
| FR-EXE-002 | TaskListWidget | フィルタロジック | TaskListWidget |
| FR-EXE-003 | ExecutionLogic | update_status() | TaskListWidget + TaskRow |
| FR-EXE-004 | ExecutionLogic | get_available_statuses() | TaskRow |
| FR-REV-001 | ReviewLogic | get_review_items() | ReviewWidget |
| FR-REV-002 | ReviewLogic | move_to_inbox() | ReviewWidget |
| FR-REV-003 | ReviewLogic | delete_item() | ReviewWidget + ConfirmDialog |
| FR-REV-004 | ReviewLogic | decompose_project() | ReviewWidget + DecomposeProjectDialog |
| FR-REV-005 | ReviewWidget | 空状態表示ロジック | ReviewWidget |
| FR-DSH-001 | DashboardWidget | 各 Logic の count 系メソッド | DashboardWidget |
| FR-DSH-002 | MatrixView | set_items() / paintEvent() | DashboardWidget |
| FR-DSH-003 | MatrixView | _calc_dot_positions() | MatrixView |
| FR-DSH-004 | MatrixView | mouseMoveEvent() | MatrixView |
| FR-DAT-001 | GtdRepository | load() / save() | MainWindow |
| FR-DAT-002 | GtdRepository | save() | MainWindow._on_data_changed() |
| FR-DAT-003 | GtdRepository | load() エラーハンドリング | - |
| FR-DAT-004 | GtdRepository | save() ディレクトリ作成 | - |
| FR-NAV-001 | MainWindow | _switch_page() | Sidebar buttons |
| FR-NAV-002 | MainWindow | _update_badges() | Sidebar buttons |
| FR-NAV-003 | MainWindow | _update_status_bar() | QStatusBar |
| FR-NAV-004 | styles.py | MAIN_STYLESHEET | MainWindow |
| FR-NAV-005 | styles.py | *_DISPLAY_NAMES | 各 Widget |

### 10.2 要件 → テスト 対応表

| 要件 ID | テストファイル | テストケース |
|---------|-------------|------------|
| FR-COL-001 | test_collection.py | test_add_to_inbox, test_add_to_inbox_with_note, test_add_to_inbox_strips_whitespace, test_add_to_inbox_empty_title_raises, test_add_to_inbox_whitespace_only_raises |
| FR-COL-002 | test_collection.py | test_move_to_someday, test_move_to_someday_nonexistent |
| FR-COL-003 | test_collection.py | test_move_to_reference, test_move_to_reference_nonexistent |
| FR-COL-004 | test_collection.py | test_delete_item, test_delete_nonexistent_item |
| FR-COL-005 | test_collection.py | test_get_inbox_items |
| FR-CLR-001 | test_clarification.py | 全 classify_as_* テスト |
| FR-CLR-002 | test_clarification.py | test_classify_as_delegation |
| FR-CLR-003 | test_clarification.py | test_classify_as_calendar |
| FR-CLR-004 | test_clarification.py | test_classify_as_project |
| FR-CLR-005 | test_clarification.py | test_classify_as_do_now |
| FR-CLR-006 | test_clarification.py | test_classify_as_task_basic, test_classify_as_task_with_context |
| FR-CLR-007 | - | GUI 手動確認 |
| FR-CLR-008 | test_clarification.py | test_classify_as_task_empty_locations |
| FR-CLR-009 | test_clarification.py | test_get_pending_items, test_get_pending_items_excludes_inbox |
| FR-ORG-001 | test_organization.py | test_set_importance_urgency, test_*_invalid_* |
| FR-ORG-002 | test_organization.py | test_get_matrix_quadrants, test_*_boundary_* |
| FR-ORG-003 | - | GUI 手動確認 |
| FR-ORG-004 | test_organization.py | test_get_unorganized_tasks |
| FR-EXE-001 | test_execution.py | test_get_active_tasks, test_get_active_tasks_includes_multiple_tags |
| FR-EXE-002 | - | GUI 手動確認 |
| FR-EXE-003 | test_execution.py | test_update_status_task, test_update_status_to_done 他 |
| FR-EXE-004 | test_execution.py | test_get_available_statuses_* |
| FR-REV-001 | test_review.py | test_get_review_items_completed, test_get_review_items_project |
| FR-REV-002 | test_review.py | test_move_to_inbox, test_move_to_inbox_nonexistent |
| FR-REV-003 | test_review.py | test_delete_item, test_delete_item_nonexistent |
| FR-REV-004 | test_review.py | test_decompose_project_success, test_decompose_project_subtask_properties, test_decompose_project_item_not_found, test_decompose_project_not_a_project, test_decompose_project_empty_titles |
| FR-REV-005 | - | GUI 手動確認 |
| FR-DSH-001 | - | GUI 手動確認（test_main_window.py で間接確認） |
| FR-DSH-002 | - | GUI 手動確認 |
| FR-DSH-003 | - | GUI 手動確認 |
| FR-DSH-004 | - | GUI 手動確認 |
| FR-DAT-001 | test_repository.py | test_save_and_load_roundtrip |
| FR-DAT-002 | test_main_window.py | test_data_changed_saves |
| FR-DAT-003 | test_repository.py | test_load_corrupted_file |
| FR-DAT-004 | test_repository.py | test_add_and_save |
| FR-NAV-001 | test_main_window.py | test_navigate_to_inbox 他 |
| FR-NAV-002 | test_main_window.py | test_badge_updates_on_data_change |
| FR-NAV-003 | test_main_window.py | test_status_bar_updates |
| FR-NAV-004 | - | GUI 手動確認 |
| FR-NAV-005 | - | GUI 手動確認 |
