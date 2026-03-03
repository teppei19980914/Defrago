#!/bin/bash
# リント・フォーマット実行スクリプト（Unix用）
# 使用方法: ./scripts/lint.sh [オプション]
# オプション:
#   --fix      自動修正を適用
#   --check    チェックのみ（修正なし）
#   --skip-install  依存関係のインストールをスキップ

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# デフォルト設定
FIX_MODE=0
SKIP_INSTALL=0
EXIT_CODE=0

# 引数の解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=1
            shift
            ;;
        --check)
            FIX_MODE=0
            shift
            ;;
        --skip-install)
            SKIP_INSTALL=1
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# 依存関係のインストール
if [[ $SKIP_INSTALL -eq 0 ]]; then
    echo "[Prep] Installing dependencies..."
    if uv sync --dev --quiet; then
        echo "  Done"
    else
        echo "  Failed to install dependencies"
        exit 1
    fi
    echo
fi

echo "========================================"
echo " Running Linter and Formatter"
echo "========================================"
echo

if [[ $FIX_MODE -eq 1 ]]; then
    echo "[1/3] Running ruff check with auto-fix..."
    uv run ruff check . --fix || EXIT_CODE=1

    echo
    echo "[2/3] Running ruff format..."
    uv run ruff format . || EXIT_CODE=1
else
    echo "[1/3] Running ruff check..."
    uv run ruff check . || EXIT_CODE=1

    echo
    echo "[2/3] Running ruff format --check..."
    uv run ruff format --check . || EXIT_CODE=1
fi

echo
echo "[3/3] Running mypy type check..."
uv run mypy src/ || EXIT_CODE=1

echo
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "========================================"
    echo " All checks passed!"
    echo "========================================"
else
    echo "========================================"
    echo " Some checks failed. Exit code: $EXIT_CODE"
    echo "========================================"
fi

exit $EXIT_CODE
