from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from database import get_db
import schemas
from services.report_service import get_monthly_summary, get_annual_rows, get_year_chart_data
from services.excel_report_service import generate_monthly_report

router = APIRouter(prefix="/api/reports", tags=["reports"])


class MonthlyTrendItem(BaseModel):
    month: int
    byproduct: int
    waste: int


@router.get("/monthly", response_model=schemas.MonthlySummary)
def monthly_report(year: int, month: int, db: Session = Depends(get_db)):
    return get_monthly_summary(year, month, db)


@router.get("/monthly/excel")
def monthly_report_excel(year: int, month: int, db: Session = Depends(get_db)):
    from urllib.parse import quote
    summary = get_monthly_summary(year, month, db)
    # 리포트 기준월까지만 포함 (당월 이후 데이터 그래프 제외)
    chart_data = {m: d for m, d in get_year_chart_data(year, db).items() if m <= month}
    path = generate_monthly_report(summary, trend_data=chart_data)
    filename = f"월말보고서_{year}년{month:02d}월.xlsx"
    encoded = quote(filename, safe="")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )


@router.get("/monthly-trend", response_model=List[MonthlyTrendItem])
def monthly_trend(year: int, db: Session = Depends(get_db)):
    """연간 월별 부산물/폐기물 합계 (차트용)"""
    result = []
    for m in range(1, 13):
        s = get_monthly_summary(year, m, db)
        result.append(MonthlyTrendItem(
            month=m,
            byproduct=s.total_current_byproduct,
            waste=s.total_current_waste,
        ))
    return result


@router.get("/annual", response_model=List[schemas.AnnualRow])
def annual_report(
    year: int,
    company_id: Optional[int] = None,
    item_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return get_annual_rows(year, company_id, item_id, db)
