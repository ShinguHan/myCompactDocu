@echo off
chcp 65001 > nul
echo ===================================================
echo   Cute Docu Shelf - 시작
echo ===================================================
echo.

REM 가상환경 확인
if not exist ".venv\Scripts\activate.bat" (
    echo [오류] 가상환경이 없습니다. install.bat 을 먼저 실행해 주세요.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

REM 이미 실행 중인 프로세스 정리
taskkill /f /im uvicorn.exe > nul 2>&1

REM 백엔드 (FastAPI) 시작 - 백그라운드
echo [1/2] 백엔드 서버 시작 중... (포트 8000)
start "CDS-Backend" /min cmd /c "call .venv\Scripts\activate.bat && cd backend && uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

REM 잠시 대기 (백엔드 준비 시간)
timeout /t 3 /nobreak > nul

REM 프론트엔드 (Streamlit) 시작
echo [2/2] 앱 시작 중... (포트 8501)
echo.
echo   브라우저가 자동으로 열립니다: http://localhost:8501
echo.
echo   종료하려면 이 창을 닫거나 Ctrl+C 를 누르세요.
echo ===================================================
streamlit run src/main.py --server.port 8501 --server.address localhost
