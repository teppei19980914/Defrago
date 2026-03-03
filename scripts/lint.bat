@echo off
REM リント・フォーマット実行スクリプト（Windows用）
REM 使用方法: scripts\lint.bat [オプション]
REM オプション:
REM   --fix      自動修正を適用
REM   --check    チェックのみ（修正なし）
REM   --skip-install  依存関係のインストールをスキップ

setlocal enabledelayedexpansion

REM プロジェクトルートに移動
cd /d "%~dp0.."

REM デフォルト設定
set FIX_MODE=0
set SKIP_INSTALL=0

REM 引数の解析
:parse_args
if "%~1"=="" goto run_install
if "%~1"=="--fix" (
    set FIX_MODE=1
    shift
    goto parse_args
)
if "%~1"=="--check" (
    set FIX_MODE=0
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

:run_lint
echo ========================================
echo  Running Linter and Formatter
echo ========================================
echo.

set EXIT_CODE=0

if %FIX_MODE%==1 (
    echo [1/3] Running ruff check with auto-fix...
    uv run ruff check . --fix
    if !ERRORLEVEL! NEQ 0 set EXIT_CODE=1

    echo.
    echo [2/3] Running ruff format...
    uv run ruff format .
    if !ERRORLEVEL! NEQ 0 set EXIT_CODE=1
) else (
    echo [1/3] Running ruff check...
    uv run ruff check .
    if !ERRORLEVEL! NEQ 0 set EXIT_CODE=1

    echo.
    echo [2/3] Running ruff format --check...
    uv run ruff format --check .
    if !ERRORLEVEL! NEQ 0 set EXIT_CODE=1
)

echo.
echo [3/3] Running mypy type check...
uv run mypy src/
if !ERRORLEVEL! NEQ 0 set EXIT_CODE=1

echo.
if %EXIT_CODE%==0 (
    echo ========================================
    echo  All checks passed!
    echo ========================================
) else (
    echo ========================================
    echo  Some checks failed. Exit code: %EXIT_CODE%
    echo ========================================
)

exit /b %EXIT_CODE%
