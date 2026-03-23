@echo off
chcp 65001 > nul
echo ===================================================
echo   Cute Docu Shelf - 시작
echo ===================================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo [오류] 가상환경이 없습니다. install.bat 을 먼저 실행해 주세요.
    pause & exit /b 1
)

if not exist "frontend\dist" (
    echo [오류] 빌드 파일이 없습니다. install.bat 을 먼저 실행해 주세요.
    pause & exit /b 1
)

call .venv\Scripts\activate.bat

echo 서버를 시작합니다...
echo 브라우저에서 http://localhost:8000 을 열어주세요.
echo 종료하려면 Ctrl+C 를 누르세요.
echo ===================================================
echo.

cd backend
uvicorn main:app --host 127.0.0.1 --port 8000
