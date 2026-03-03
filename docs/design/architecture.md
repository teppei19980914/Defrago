# MindFlow アーキテクチャ設計書

更新日: 2026-03-03

## 概要

MindFlowは、GTD（Getting Things Done）手法に基づくタスク管理GUIアプリケーションである。
重要度×緊急度マトリクスによるタスクの可視化を中核機能とし、5つのGTDフェーズをサポートする。

## システム構成図

```mermaid
graph TB
    subgraph GUI Layer
        MW[MainWindow]
        DW[DashboardWidget]
        IW[InboxWidget]
        CW[ClarificationWidget]
        OW[OrganizationWidget]
        TW[TaskListWidget]
        RW[ReviewWidget]
    end

    subgraph Logic Layer
        CL[CollectionLogic]
        CLR[ClarificationLogic]
        OL[OrganizationLogic]
        EL[ExecutionLogic]
        RL[ReviewLogic]
    end

    subgraph Data Layer
        M[GtdItem / Enums]
        R[GtdRepository]
        J[(JSON File)]
    end

    MW --> DW & IW & CW & OW & TW & RW
    IW --> CL
    CW --> CLR
    OW --> OL
    TW --> EL
    RW --> RL
    DW --> OL

    CL & CLR & OL & EL & RL --> R
    R --> M
    R --> J
```

## レイヤー設計

### 1. Data Layer (Model)

- **models.py**: StrEnumによる状態定義とdataclassによるGtdItemデータモデル
- **repository.py**: JSONファイルへのCRUD操作。アイテムのシリアライズ/デシリアライズ

### 2. Logic Layer (Controller)

各GTDフェーズに対応するロジッククラス:

| クラス | 責務 |
|--------|------|
| CollectionLogic | Inbox登録、削除、参考資料/いつかやるへの分類 |
| ClarificationLogic | GTD決定木に基づくタスク分類、Context設定 |
| OrganizationLogic | 重要度/緊急度設定、4象限マトリクス分類 |
| ExecutionLogic | タスクステータス変更、バリデーション |
| ReviewLogic | 完了タスクの削除/Inbox戻し |

### 3. GUI Layer (View)

- **MainWindow**: サイドバーナビゲーション + QStackedWidgetによるページ切替
- **各ウィジェット**: 対応するロジッククラスを使用してUI操作を実行
- **components/**: ItemCard, MatrixView, ConfirmDialog等の再利用コンポーネント

## データモデル

```mermaid
classDiagram
    class GtdItem {
        +str id
        +str title
        +str created_at
        +str updated_at
        +ItemStatus item_status
        +Tag tag
        +str status
        +list~Location~ locations
        +TimeEstimate time_estimate
        +EnergyLevel energy
        +int importance
        +int urgency
        +str note
        +touch()
        +is_task() bool
        +is_done() bool
        +needs_organization() bool
        +needs_review() bool
    }

    class ItemStatus {
        INBOX
        SOMEDAY
        REFERENCE
    }

    class Tag {
        DELEGATION
        CALENDAR
        PROJECT
        DO_NOW
        TASK
    }
```

## データフロー

### 収集フロー
```
User Input → CollectionLogic.add_to_inbox() → GtdRepository.add() → JSON保存
```

### 明確化フロー
```
GTD決定木 → ClarificationLogic.classify_as_*() → tag/status設定 → JSON保存
```

### 整理フロー
```
スライダー入力 → OrganizationLogic.set_importance_urgency() → JSON保存
```

## 永続化

- 保存先: `~/.mindflow/gtd_data.json`
- エンコーディング: UTF-8
- フォーマット: JSON配列（pretty-print、indent=2）
- 保存タイミング: データ変更時に即時保存（data_changedシグナル経由）
