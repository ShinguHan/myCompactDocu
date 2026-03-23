@echo off
chcp 65001 > nul
echo Cute Docu Shelf 서버를 종료합니다...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a > nul 2>&1
)
echo 종료 완료.
timeout /t 2 /nobreak > nul
