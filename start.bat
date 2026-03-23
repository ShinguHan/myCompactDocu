@echo off
echo ===================================================
echo   Cute Docu Shelf - Start
echo ===================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Please run install.bat first.
    pause & exit /b 1
)

if not exist "frontend\dist" (
    echo [ERROR] Build files not found. Please run install.bat first.
    pause & exit /b 1
)

call .venv\Scripts\activate.bat

echo Starting server...
echo Open http://localhost:8000 in your browser.
echo Press Ctrl+C to stop.
echo ===================================================
echo.

cd backend
uvicorn main:app --host 127.0.0.1 --port 8000
