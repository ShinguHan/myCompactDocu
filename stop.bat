@echo off
chcp 65001 > nul
echo ===================================================
echo   Cute Docu Shelf - 종료
echo ===================================================
echo.

echo 실행 중인 서버를 종료합니다...

REM 백엔드 (uvicorn) 종료
taskkill /f /fi "WINDOWTITLE eq CDS-Backend*" > nul 2>&1
taskkill /f /im uvicorn.exe > nul 2>&1

REM 프론트엔드 (streamlit) 종료
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8501 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a > nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a > nul 2>&1
)

echo 종료 완료.
timeout /t 2 /nobreak > nul
