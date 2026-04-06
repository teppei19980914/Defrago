#!/bin/bash
# SessionStart hook: mainブランチで開発していないか確認
# mainの場合、stdoutにメッセージを出力しClaudeのコンテキストに注入する

cd "$CLAUDE_PROJECT_DIR" || exit 0

BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null)

if [ "$BRANCH" = "main" ]; then
    cat <<MSG
WARNING: 現在mainブランチです。mainでの直接開発は禁止されています。
開発を開始する前に、必ずブランチを作成してください。

ブランチ命名規約:
  - 機能追加: feature/xxx
  - バグ修正: fix/xxx
  - リリース: release/vX.Y.Z
  - ドキュメント: docs/xxx

例: git checkout -b feature/new-feature

ユーザーにブランチ作成を提案してください。
MSG
fi

exit 0
