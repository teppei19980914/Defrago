---
name: logging
description: ログ出力ルール。ログレベルの使い分け、フォーマット、ファイル管理方針を含む。
---

# ログ出力ルール

すべてのツール・モジュールには、ユーザーからの問い合わせ対応（特に不具合調査）のためにログ出力機能を実装すること。

## 必須事項

1. **ログ出力の実装**: すべてのモジュールで `logging` を使用する
2. **ファイル出力**: ログはリポジトリ内の `logs/` ディレクトリに保存する
3. **適切なログレベル**: 状況に応じたログレベルを使用する

## ログレベルの使い分け

| レベル | 用途 |
|--------|------|
| `DEBUG` | 開発時のデバッグ情報（変数値、処理フロー等） |
| `INFO` | 正常な処理の記録（開始、終了、重要なステップ） |
| `WARNING` | 注意が必要だが処理は継続可能な状況 |
| `ERROR` | エラー発生（処理失敗、例外キャッチ等） |
| `CRITICAL` | システム停止レベルの重大エラー |

## ログ設定の実装

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

## ログフォーマット

```
2024-01-15 10:30:45.123 | INFO     | module_name:function_name:42 | メッセージ
```

フォーマット要素：
- **タイムスタンプ**: ミリ秒まで記録
- **ログレベル**: 見やすく固定幅
- **モジュール名**: 問題箇所の特定用
- **関数名・行番号**: デバッグ時の追跡用
- **メッセージ**: 具体的な内容

## 実装例

```python
import logging
from study_python.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

def process_user_data(user_id: int, data: dict) -> bool:
    """ユーザーデータを処理する。"""
    logger.info(f"Processing data for user_id={user_id}")
    logger.debug(f"Input data: {data}")

    try:
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

## ログファイル管理

- **保存先**: リポジトリルートの `logs/` ディレクトリ（.gitignoreに含める）
- **ファイル名**: `app_YYYY-MM-DD.log`（日付ローテーション）
- **保持期間**: 30日間（古いログは自動削除）
- **最大サイズ**: 10MB（サイズローテーション）

## 注意事項

- 機密情報（パスワード、トークン等）はログに出力しない
- 大量データはログに出力せず、件数やサマリーを記録する
- 本番環境では `INFO` 以上、開発環境では `DEBUG` 以上を出力する
