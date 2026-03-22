@echo off
setlocal EnableExtensions
chcp 65001 >nul
title AI Daily

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "VENV_DIR=%ROOT%.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"
set "FRONTEND_DIST=%ROOT%frontend\dist\index.html"

echo ========================================
echo   AI Daily - Starting...
echo ========================================
echo.

echo [1/5] Checking Python environment...
call :ensure_venv
if errorlevel 1 goto :fail

echo [2/5] Checking Python deps...
"%VENV_PIP%" install -q -r requirements.txt
if errorlevel 1 (
    echo   Failed to install Python dependencies.
    goto :fail
)

echo [3/5] Building frontend...
pushd frontend >nul
call npm.cmd run build
set "BUILD_EXIT=%ERRORLEVEL%"
popd >nul
if not "%BUILD_EXIT%"=="0" (
    if exist "%FRONTEND_DIST%" (
        echo   Frontend build failed. Reusing existing dist.
    ) else (
        echo   Frontend build failed and no existing dist was found.
        goto :fail
    )
)

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set "TODAY=%%i"
set "REPORT=%ROOT%output\%TODAY%.json"
set "STATE=%ROOT%data\state.json"

if /I "%~1"=="refresh" (
    echo [4/5] Force refresh: clearing state...
    if exist "%REPORT%" del "%REPORT%"
    if exist "%STATE%" del "%STATE%"
)

if not exist "%REPORT%" (
    echo [4/5] Fetching today's AI news ^(%TODAY%^)...
    "%VENV_PY%" main.py
    if errorlevel 1 (
        echo   Pipeline failed.
        goto :fail
    )
    echo   Pipeline complete!
) else (
    echo [4/5] Today's data exists, skipping. Run with "refresh" to re-fetch.
)

echo [5/5] Starting server...
echo.
echo   URL: http://localhost:8000
echo   Close this window to stop
echo.
start "" http://localhost:8000
"%VENV_PY%" -m uvicorn src.server.main:app --host 127.0.0.1 --port 8000
goto :eof

:ensure_venv
if exist "%VENV_PY%" (
    "%VENV_PY%" -c "import sys" >nul 2>&1
    if not errorlevel 1 (
        echo   Using existing .venv
        exit /b 0
    )
    echo   Existing .venv is broken. Attempting rebuild...
) else (
    echo   .venv not found. Creating...
)

call :find_bootstrap_python
if errorlevel 1 exit /b 1

%BOOTSTRAP_PY% -m venv "%VENV_DIR%" --clear
if errorlevel 1 (
    echo   Failed to create .venv with %BOOTSTRAP_PY%.
    exit /b 1
)

"%VENV_PY%" -c "import sys" >nul 2>&1
if errorlevel 1 (
    echo   Created .venv but python.exe is still unusable.
    exit /b 1
)

echo   .venv is ready.
exit /b 0

:find_bootstrap_python
set "BOOTSTRAP_PY="
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "BOOTSTRAP_PY=py -3"
    exit /b 0
)

python -c "import sys" >nul 2>&1
if not errorlevel 1 (
    set "BOOTSTRAP_PY=python"
    exit /b 0
)

echo   No working system Python was found.
echo   Install Python 3.11+ and re-run this launcher.
exit /b 1

:fail
echo.
echo Startup aborted.
pause
exit /b 1
