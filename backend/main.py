from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine, Base
import models  # noqa: F401 - triggers table creation

from routers import items, companies, item_companies, contracts, transactions, reports, exit_passes

# DB 테이블 생성 (없는 경우에만)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cute Docu Shelf API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(items.router)
app.include_router(companies.router)
app.include_router(item_companies.router)
app.include_router(contracts.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(exit_passes.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


# 프로덕션: React 빌드 파일 서빙
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
