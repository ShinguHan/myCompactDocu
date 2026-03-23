@echo off
chcp 65001 > nul
echo ===================================================
echo   Cute Docu Shelf - 설치
echo ===================================================
echo.

REM ── Python 확인 ──────────────────────────────────────────────────────────────
python --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo       https://www.python.org 에서 Python 3.11 이상을 설치해 주세요.
    pause & exit /b 1
)

REM ── Node.js 확인 ─────────────────────────────────────────────────────────────
node --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Node.js가 설치되어 있지 않습니다.
    echo       https://nodejs.org 에서 LTS 버전을 설치해 주세요.
    pause & exit /b 1
)

REM ── Python 가상환경 ───────────────────────────────────────────────────────────
echo [1/4] Python 가상환경 생성 중...
if not exist ".venv" python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
if errorlevel 1 ( echo [오류] Python 패키지 설치 실패 & pause & exit /b 1 )
echo       완료

REM ── React 빌드 ────────────────────────────────────────────────────────────────
echo [2/4] 프론트엔드 패키지 설치 중...
cd frontend
call npm install --silent
if errorlevel 1 ( echo [오류] npm install 실패 & pause & exit /b 1 )
echo       완료

echo [3/4] 프론트엔드 빌드 중...
call npm run build
if errorlevel 1 ( echo [오류] 빌드 실패 & pause & exit /b 1 )
cd ..
echo       완료

REM ── 출력 폴더 ────────────────────────────────────────────────────────────────
echo [4/4] 폴더 초기화...
if not exist "output" mkdir output
echo       완료

echo.
echo ===================================================
echo   설치 완료!  start.bat 으로 실행하세요.
echo ===================================================
pause
