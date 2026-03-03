@echo off
REM 全チェック実行スクリプト（Windows用）
REM リント、フォーマット、型チェック、テストをすべて実行
REM 使用方法: scripts\check-all.bat [オプション]
REM オプション:
REM   --fix   リント・フォーマットの自動修正を適用
REM   --cov   テスト時にカバレッジを取得（HTMLレポート生成）
REM   --skip-install  依存関係のインストールをスキップ

setlocal enabledelayedexpansion

REM プロジェクトルートに移動
cd /d "%~dp0.."

REM デフォルト設定（高速モード）
set FIX_MODE=0
set COV_ENABLED=0
set SKIP_INSTALL=0

REM 引数の解析
:parse_args
if "%~1"=="" goto run_install
if "%~1"=="--fix" (
    set FIX_MODE=1
    shift
    goto parse_args
)
if "%~1"=="--cov" (
    set COV_ENABLED=1
    shift
    goto parse_args
)
if "%~1"=="--skip-install" (
    set SKIP_INSTALL=1
    shift
    goto parse_args
)
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

:run_checks
echo ========================================
echo  Running All Checks
echo ========================================
echo.

set TOTAL_EXIT_CODE=0

REM Step 1: Lint
echo [Step 1/4] Ruff Check
if %FIX_MODE%==1 (
    uv run ruff check . --fix
) else (
    uv run ruff check .
)
if !ERRORLEVEL! NEQ 0 (
    echo   FAILED
    set TOTAL_EXIT_CODE=1
) else (
    echo   PASSED
)
echo.

REM Step 2: Format
echo [Step 2/4] Ruff Format
if %FIX_MODE%==1 (
    uv run ruff format .
) else (
    uv run ruff format --check .
)
if !ERRORLEVEL! NEQ 0 (
    echo   FAILED
    set TOTAL_EXIT_CODE=1
) else (
    echo   PASSED
)
echo.

REM Step 3: Type Check
echo [Step 3/4] Mypy Type Check
uv run mypy src/
if !ERRORLEVEL! NEQ 0 (
    echo   FAILED
    set TOTAL_EXIT_CODE=1
) else (
    echo   PASSED
)
echo.

REM Step 4: Tests
echo [Step 4/4] Pytest
if %COV_ENABLED%==1 (
    echo Coverage: ENABLED
    uv run pytest -v --cov=src/study_python --cov-report=term-missing --cov-report=html
) else (
    echo Coverage: DISABLED ^(use --cov to enable^)
    uv run pytest -v
)
if !ERRORLEVEL! NEQ 0 (
    echo   FAILED
    set TOTAL_EXIT_CODE=1
) else (
    echo   PASSED
)
echo.

REM Summary
echo ========================================
if %TOTAL_EXIT_CODE%==0 (
    echo  All checks passed!
    if %COV_ENABLED%==1 (
        echo  Coverage report: htmlcov/index.html
    )
) else (
    echo  Some checks failed!
)
echo ========================================

exit /b %TOTAL_EXIT_CODE%
