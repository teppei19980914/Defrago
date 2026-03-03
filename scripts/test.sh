#!/bin/bash
# ユニットテスト実行スクリプト（Unix用）- 高速版
# 使用方法: ./scripts/test.sh [オプション]
# オプション:
#   --verbose  詳細出力
#   --fast     最初の失敗で停止
#   --skip-install  依存関係のインストールをスキップ
#
# カバレッジ付きで実行したい場合は test-full.sh を使用してください。

set -e

# プロジェクトルートに移動
cd "$(dirname "$0")/.."

# デフォルト設定
PYTEST_ARGS="-v"
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
echo " Running Unit Tests (Fast Mode)"
echo "========================================"
echo

if uv run pytest $PYTEST_ARGS; then
    echo
    echo "========================================"
    echo " All tests passed!"
    echo " Tip: Use test-full.sh for coverage"
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
