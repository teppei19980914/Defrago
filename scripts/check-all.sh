#!/bin/bash
# 全チェック実行スクリプト（Unix用）
# リント、フォーマット、型チェック、テストをすべて実行
# 使用方法: ./scripts/check-all.sh [オプション]
# オプション:
#   --fix   リント・フォーマットの自動修正を適用
#   --cov   テスト時にカバレッジを取得（HTMLレポート生成）
#   --skip-install  依存関係のインストールをスキップ

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# デフォルト設定（高速モード）
FIX_MODE=0
COV_ENABLED=0
SKIP_INSTALL=0
TOTAL_EXIT_CODE=0

# 引数の解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix)
            FIX_MODE=1
            shift
            ;;
        --cov)
            COV_ENABLED=1
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
echo " Running All Checks"
echo "========================================"
echo

# Step 1: Lint
echo "[Step 1/4] Ruff Check"
if [[ $FIX_MODE -eq 1 ]]; then
    if uv run ruff check . --fix; then
        echo "  PASSED"
    else
        echo "  FAILED"
        TOTAL_EXIT_CODE=1
    fi
else
    if uv run ruff check .; then
        echo "  PASSED"
    else
        echo "  FAILED"
        TOTAL_EXIT_CODE=1
    fi
fi
echo

# Step 2: Format
echo "[Step 2/4] Ruff Format"
if [[ $FIX_MODE -eq 1 ]]; then
    if uv run ruff format .; then
        echo "  PASSED"
    else
        echo "  FAILED"
        TOTAL_EXIT_CODE=1
    fi
else
    if uv run ruff format --check .; then
        echo "  PASSED"
    else
        echo "  FAILED"
        TOTAL_EXIT_CODE=1
    fi
fi
echo

# Step 3: Type Check
echo "[Step 3/4] Mypy Type Check"
if uv run mypy src/; then
    echo "  PASSED"
else
    echo "  FAILED"
    TOTAL_EXIT_CODE=1
fi
echo

# Step 4: Tests
echo "[Step 4/4] Pytest"
if [[ $COV_ENABLED -eq 1 ]]; then
    echo "Coverage: ENABLED"
    if uv run pytest -v --cov=src/study_python --cov-report=term-missing --cov-report=html; then
        echo "  PASSED"
    else
        echo "  FAILED"
        TOTAL_EXIT_CODE=1
    fi
else
    echo "Coverage: DISABLED (use --cov to enable)"
    if uv run pytest -v; then
        echo "  PASSED"
    else
        echo "  FAILED"
        TOTAL_EXIT_CODE=1
    fi
fi
echo

# Summary
echo "========================================"
if [[ $TOTAL_EXIT_CODE -eq 0 ]]; then
    echo " All checks passed!"
    if [[ $COV_ENABLED -eq 1 ]]; then
        echo " Coverage report: htmlcov/index.html"
    fi
else
    echo " Some checks failed!"
fi
echo "========================================"

exit $TOTAL_EXIT_CODE
