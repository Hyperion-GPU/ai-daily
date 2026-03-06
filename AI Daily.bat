@echo off
chcp 65001 >nul
title AI Daily

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo ========================================
echo   AI Daily - Starting...
echo ========================================
echo.

:: 1. Activate venv
if exist ".venv\Scripts\activate.bat" (
    echo [1/5] Activating venv...
    call ".venv\Scripts\activate.bat"
) else (
    echo [1/5] Creating venv...
    python -m venv .venv
    call ".venv\Scripts\activate.bat"
)

:: 2. Install deps
echo [2/5] Checking Python deps...
pip install -q -r requirements.txt

:: 3. Build frontend
echo [3/5] Building frontend...
cd frontend
call npm run build
cd /d "%ROOT%"

:: 4. Run pipeline if today's data doesn't exist
for /f "tokens=1-3 delims=/ " %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%a
set "REPORT=%ROOT%output\%TODAY%.json"
set "STATE=%ROOT%data\state.json"

if "%1"=="refresh" (
    echo [4/5] Force refresh: clearing state...
    if exist "%REPORT%" del "%REPORT%"
    if exist "%STATE%" del "%STATE%"
)

if not exist "%REPORT%" (
    echo [4/5] Fetching today's AI news ^(%TODAY%^)...
    python main.py
    echo   Pipeline complete!
) else (
    echo [4/5] Today's data exists, skipping. Run with "refresh" to re-fetch.
)

:: 5. Open browser and start server
echo [5/5] Starting server...
echo.
echo   URL: http://localhost:8000
echo   Close this window to stop
echo.
start http://localhost:8000
python -m uvicorn src.server.main:app --host 127.0.0.1 --port 8000 --reload
