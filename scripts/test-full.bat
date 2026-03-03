@echo off
REM ユニットテスト実行スクリプト（Windows用）- カバレッジ付き
REM 使用方法: scripts\test-full.bat [オプション]
REM オプション:
REM   --verbose  詳細出力
REM   --fast     最初の失敗で停止
REM   --skip-install  依存関係のインストールをスキップ
REM
REM カバレッジを取得し、HTMLレポートを生成します。
REM レポートは htmlcov/index.html で確認できます。
REM
REM 高速に実行したい場合は test.bat を使用してください。

setlocal enabledelayedexpansion

REM プロジェクトルートに移動
cd /d "%~dp0.."

REM デフォルト設定（カバレッジ有効）
set PYTEST_ARGS=-v --cov=src/study_python --cov-report=term-missing --cov-report=html
set SKIP_INSTALL=0

REM 引数の解析
:parse_args
if "%~1"=="" goto run_install
if "%~1"=="--verbose" (
    set PYTEST_ARGS=!PYTEST_ARGS! -vv
    shift
    goto parse_args
)
if "%~1"=="--fast" (
    set PYTEST_ARGS=!PYTEST_ARGS! -x
    shift
    goto parse_args
)
if "%~1"=="--skip-install" (
    set SKIP_INSTALL=1
    shift
    goto parse_args
)
REM 不明な引数はそのまま渡す
set PYTEST_ARGS=!PYTEST_ARGS! %~1
shift
goto parse_args

:run_install
REM 依存関係のインストール
if %SKIP_INSTALL%==0 (
    echo [Prep] Installing dependencies...
    uv sync --dev --quiet
    if !ERRORLEVEL! NEQ 0 (
        echo   Failed to install dependencies
        exit /b 1
    )
    echo   Done
    echo.
)

:run_tests
echo ========================================
echo  Running Unit Tests with Coverage
echo ========================================
echo  HTML report: htmlcov/index.html
echo ========================================
echo.

uv run pytest %PYTEST_ARGS%
set TEST_EXIT_CODE=%ERRORLEVEL%

echo.
if %TEST_EXIT_CODE% EQU 0 (
    echo ========================================
    echo  All tests passed!
    echo  Coverage report: htmlcov/index.html
    echo ========================================
) else (
    echo ========================================
    echo  Some tests failed. Exit code: %TEST_EXIT_CODE%
    echo ========================================
)

exit /b %TEST_EXIT_CODE%
