@echo off
chcp 65001 > nul
echo ===================================================
echo   Cute Docu Shelf - 설치
echo ===================================================
echo.

REM Python 설치 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo       https://www.python.org 에서 Python 3.11 이상을 설치해 주세요.
    pause
    exit /b 1
)

echo [1/3] 가상환경 생성 중...
if not exist ".venv" (
    python -m venv .venv
    if errorlevel 1 (
        echo [오류] 가상환경 생성 실패
        pause
        exit /b 1
    )
)
echo       완료

echo [2/3] 패키지 설치 중...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
if errorlevel 1 (
    echo [오류] 패키지 설치 실패
    pause
    exit /b 1
)
echo       완료

echo [3/3] 출력 폴더 생성...
if not exist "output" mkdir output
echo       완료

echo.
echo ===================================================
echo   설치 완료! start.bat 으로 프로그램을 실행하세요.
echo ===================================================
pause
