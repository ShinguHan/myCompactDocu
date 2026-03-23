@echo off
echo Stopping Cute Docu Shelf server...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a > nul 2>&1
)
echo Server stopped.
timeout /t 2 /nobreak > nul
