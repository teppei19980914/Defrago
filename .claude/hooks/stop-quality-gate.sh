#!/bin/bash
# Stop hook: 応答完了時にPythonファイルの変更があればlint/format違反を検出

cd "$CLAUDE_PROJECT_DIR" || exit 0

# git diffでPythonファイルの変更があるか確認
CHANGED_PY=$(git diff --name-only --diff-filter=ACMR 2>/dev/null | grep '\.py$' || true)
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACMR 2>/dev/null | grep '\.py$' || true)
UNTRACKED_PY=$(git ls-files --others --exclude-standard 2>/dev/null | grep '\.py$' || true)

ALL_PY=$(echo -e "${CHANGED_PY}\n${STAGED_PY}\n${UNTRACKED_PY}" | sort -u | grep -v '^$' || true)

# 変更されたPythonファイルがなければスキップ
if [[ -z "$ALL_PY" ]]; then
  exit 0
fi

ERRORS=""

# ruff check
LINT_RESULT=$(echo "$ALL_PY" | xargs uv run ruff check 2>/dev/null || true)
if [[ -n "$LINT_RESULT" ]]; then
  ERRORS="${ERRORS}[lint違反あり] uv run ruff check . で確認してください\n"
fi

# ruff format check
FORMAT_RESULT=$(echo "$ALL_PY" | xargs uv run ruff format --check 2>&1 || true)
if echo "$FORMAT_RESULT" | grep -q 'would reformat'; then
  ERRORS="${ERRORS}[format違反あり] uv run ruff format . で修正してください\n"
fi

if [[ -n "$ERRORS" ]]; then
  echo -e "品質チェック警告:\n$ERRORS" >&2
fi

exit 0
