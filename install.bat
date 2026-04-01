@echo off
echo ===================================================
echo   Cute Docu Shelf - Install
echo ===================================================
echo.

REM ── Check Python ─────────────────────────────────────────────────────────────
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo        Please install Python 3.11 or later from https://www.python.org
    pause & exit /b 1
)

REM ── Python virtual environment ───────────────────────────────────────────────
echo [1/2] Creating Python virtual environment...
if not exist ".venv" python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
if errorlevel 1 ( echo [ERROR] Failed to install Python packages & pause & exit /b 1 )
echo       Done

REM ── Output folders ───────────────────────────────────────────────────────────
echo [2/2] Initializing folders...
if not exist "output" mkdir output
if not exist "images" mkdir images
echo       Done

echo.
echo ===================================================
echo   Installation complete! Run start.bat to launch.
echo ===================================================
pause
