# Cute Docu Shelf

부산물 매각 및 폐기물 처리 현황 관리 시스템

## 기술 스택

| 구분 | 기술 |
|---|---|
| 백엔드 | Python · FastAPI · SQLAlchemy · SQLite |
| 프론트엔드 | React · TypeScript · Vite |
| Excel 보고서 | openpyxl |

---

## 설치 및 실행 (Windows)

### 사전 요구사항

- [Python 3.11+](https://www.python.org/downloads/) — 설치 시 **"Add Python to PATH"** 반드시 체크
- [Node.js LTS](https://nodejs.org/) — 프론트엔드 빌드용

### 최초 설치 (1회만)

```
install.bat 더블클릭
```

자동으로 진행됩니다:
1. Python 가상환경 생성 및 패키지 설치
2. React 프론트엔드 빌드
3. 출력 폴더(output/) 생성

### 실행

```
start.bat 더블클릭
```

브라우저에서 **http://localhost:8000** 접속

### 종료

- `start.bat` 실행 창에서 `Ctrl+C`
- 또는 `stop.bat` 더블클릭

---

## 데이터 임포트 방법

### Excel 파일 형식

매각/처리 현황 Excel 파일 (부산물·폐기물 거래 내역)

### 방법 1 — 앱에서 직접 임포트 (권장)

1. 브라우저에서 앱 실행 → **원장** 또는 **데이터 관리** 메뉴
2. **Excel 임포트** 버튼 클릭
3. 파일 선택 → 미리보기 확인 (중복 제외 건수 표시)
4. **확인** 버튼으로 최종 반영

### 방법 2 — migrate 스크립트 직접 실행

대량 데이터(연간 전체) 임포트 시 사용:

```cmd
REM 가상환경 활성화
.venv\Scripts\activate.bat

REM backend 폴더로 이동 후 실행
cd backend
python migrate_from_excel.py
```

> **주의**: 중복 체크 후 삽입되므로 여러 번 실행해도 안전합니다.

### 임포트 후 확인

- 앱 → **원장** 메뉴에서 데이터 조회
- **월말 보고서** 메뉴 → 해당 월 선택 → Excel 다운로드

---

## 폴더 구조

```
├── backend/              # FastAPI 서버
│   ├── main.py           # 진입점 (uvicorn으로 실행)
│   ├── models.py         # DB 모델
│   ├── schemas.py        # API 스키마
│   ├── database.py       # DB 연결 (SQLite: cute_docu_shelf.db)
│   ├── routers/          # API 라우터
│   ├── services/
│   │   ├── report_service.py       # 월별 집계
│   │   ├── excel_report_service.py # Excel 보고서 생성
│   │   └── import_service.py       # Excel 데이터 임포트
│   └── templates/
│       └── report_template.xlsx    # 월말 보고서 템플릿
├── frontend/             # React 앱 (빌드 후 backend가 서빙)
├── output/               # 생성된 보고서 저장 위치
├── cute_docu_shelf.db    # SQLite DB
├── install.bat           # 최초 설치
├── start.bat             # 서버 시작
└── stop.bat              # 서버 종료
```

---

## DB 백업

`cute_docu_shelf.db` 파일을 복사해두면 됩니다.

---

## API 문서

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI로 API 확인 가능
