#!/bin/bash
# ユニットテスト実行スクリプト（Unix用）- カバレッジ付き
# 使用方法: ./scripts/test-full.sh [オプション]
# オプション:
#   --verbose  詳細出力
#   --fast     最初の失敗で停止
#   --skip-install  依存関係のインストールをスキップ
#
# カバレッジを取得し、HTMLレポートを生成します。
# レポートは htmlcov/index.html で確認できます。
#
# 高速に実行したい場合は test.sh を使用してください。

set -e

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# デフォルト設定（カバレッジ有効）
PYTEST_ARGS="-v --cov=src/study_python --cov-report=term-missing --cov-report=html"
SKIP_INSTALL=0

# 引数の解析
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose)
            PYTEST_ARGS="$PYTEST_ARGS -vv"
            shift
            ;;
        --fast)
            PYTEST_ARGS="$PYTEST_ARGS -x"
            shift
            ;;
        --skip-install)
            SKIP_INSTALL=1
            shift
            ;;
        *)
            # 不明な引数はそのまま渡す
            PYTEST_ARGS="$PYTEST_ARGS $1"
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
echo " Running Unit Tests with Coverage"
echo "========================================"
echo " HTML report: htmlcov/index.html"
echo "========================================"
echo

if uv run pytest $PYTEST_ARGS; then
    echo
    echo "========================================"
    echo " All tests passed!"
    echo " Coverage report: htmlcov/index.html"
    echo "========================================"
    exit 0
else
    EXIT_CODE=$?
    echo
    echo "========================================"
    echo " Some tests failed. Exit code: $EXIT_CODE"
    echo "========================================"
    exit $EXIT_CODE
fi
