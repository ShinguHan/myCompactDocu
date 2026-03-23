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

REM ── Check Node.js ────────────────────────────────────────────────────────────
node --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed.
    echo        Please install the LTS version from https://nodejs.org
    pause & exit /b 1
)

REM ── Python virtual environment ───────────────────────────────────────────────
echo [1/4] Creating Python virtual environment...
if not exist ".venv" python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
if errorlevel 1 ( echo [ERROR] Failed to install Python packages & pause & exit /b 1 )
echo       Done

REM ── React build ──────────────────────────────────────────────────────────────
echo [2/4] Installing frontend packages...
cd frontend
call npm install --silent
if errorlevel 1 ( echo [ERROR] npm install failed & pause & exit /b 1 )
echo       Done

echo [3/4] Building frontend...
call npm run build
if errorlevel 1 ( echo [ERROR] Build failed & pause & exit /b 1 )
cd ..
echo       Done

REM ── Output folder ────────────────────────────────────────────────────────────
echo [4/4] Initializing folders...
if not exist "output" mkdir output
echo       Done

echo.
echo ===================================================
echo   Installation complete! Run start.bat to launch.
echo ===================================================
pause
