#!/bin/bash
# PostToolUse hook: Edit/Write後にPythonファイルを自動リント・フォーマット

FILE_PATH=$(python -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Pythonファイル以外、または存在しないファイルはスキップ
if [[ -z "$FILE_PATH" || "$FILE_PATH" != *.py || ! -f "$FILE_PATH" ]]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR" || exit 0
uv run ruff check --fix "$FILE_PATH" 2>/dev/null
uv run ruff format "$FILE_PATH" 2>/dev/null

exit 0
