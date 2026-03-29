#!/bin/bash
# PreToolUse hook: 危険なBashコマンドをブロック

COMMAND=$(python -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# 危険なコマンドパターンをチェック
DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf \."
  "rm -rf \*"
  "git push.*--force.*main"
  "git push.*--force.*master"
  "git reset --hard"
  "git clean -fd"
  "> /dev/sda"
  "mkfs\."
  "dd if=.*/dev/"
  ":(){.*};:"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qE "$pattern"; then
    echo "BLOCKED: 危険なコマンドを検出しました: $COMMAND" >&2
    echo "このコマンドはHookによりブロックされました。" >&2
    exit 2
  fi
done

exit 0
