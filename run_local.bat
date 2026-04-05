@echo off

cd /d "%~dp0"

set SECRET_KEY=local-dev-secret-key
set DATABASE_URL=sqlite:///./mindflow_local.db
set DEBUG=true
set PORT=8080

echo ========================================
echo   MindFlow - Local Dev
echo ========================================
echo.

REM Kill any existing process on the port
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT%.*LISTENING"') do (
    echo Port %PORT% is in use by PID %%a. Killing...
    taskkill /PID %%a /F >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo [1/3] uv sync...
call uv sync --extra dev >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv sync failed
    pause
    exit /b 1
)
echo       OK
echo.

echo [2/3] pytest...
call uv run pytest tests/ -x -q --tb=short
if errorlevel 1 (
    echo.
    echo ERROR: Tests failed
    pause
    exit /b 1
)
echo.

echo [3/3] Starting server...
echo.
echo   URL: http://localhost:%PORT%
echo   Stop: Ctrl+C
echo ========================================
echo.

start "" http://localhost:%PORT%
call uv run uvicorn study_python.gtd.web.app:app --host 0.0.0.0 --port %PORT% --reload

pause
