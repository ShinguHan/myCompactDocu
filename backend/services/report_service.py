from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract
from typing import Optional, List
from datetime import date

import models
import schemas


def get_monthly_summary(year: int, month: int, db: Session) -> schemas.MonthlySummary:
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    def _query_month(y, m):
        return (
            db.query(models.Transaction)
            .options(
                joinedload(models.Transaction.item),
                joinedload(models.Transaction.company),
            )
            .filter(
                extract("year", models.Transaction.date) == y,
                extract("month", models.Transaction.date) == m,
            )
            .all()
        )

    curr_txs = _query_month(year, month)
    prev_txs = _query_month(prev_year, prev_month)

    # 전월 집계: (company, item) → total_amount
    prev_map: dict = {}
    for tx in prev_txs:
        key = (tx.company.name, tx.item.report_name or tx.item.name)
        prev_map[key] = prev_map.get(key, 0) + tx.total_amount

    # 당월 집계
    curr_map: dict = {}
    for tx in curr_txs:
        key = (tx.company.name, tx.item.report_name or tx.item.name, tx.item.category, tx.unit_price)
        factor = tx.item.kg_per_unit or 1.0
        if key not in curr_map:
            curr_map[key] = {
                "qty": 0, "amt": 0, "ea": 0,
                "has_factor": tx.item.kg_per_unit is not None,
                "unit": tx.item.unit,
            }
        curr_map[key]["qty"] += tx.quantity * factor  # 보고서 표시용 kg 환산
        curr_map[key]["ea"]  += tx.quantity           # 원래 EA/대 수량 (비고란)
        curr_map[key]["amt"] += tx.total_amount

    byproducts: List[schemas.ReportRow] = []
    wastes: List[schemas.ReportRow] = []

    for (company_name, item_name, category, unit_price), v in sorted(curr_map.items()):
        prev_amt = prev_map.get((company_name, item_name), 0)
        if v["has_factor"]:
            note = f"{int(v['ea'])} EA"
        elif v["unit"] == "원/대" and unit_price and v["amt"]:
            trucks = int(round(abs(v["amt"]) / abs(unit_price)))
            note = f"차량대수:{trucks}대"
        else:
            note = None
        row = schemas.ReportRow(
            company_name=company_name,
            item_name=item_name,
            unit_price=unit_price,
            current_quantity=v["qty"],
            current_amount=v["amt"],
            prev_amount=prev_amt,
            note=note,
        )
        if category == models.CategoryEnum.byproduct:
            byproducts.append(row)
        else:
            wastes.append(row)

    # 전월에만 있는 데이터도 포함
    curr_keys = {(c, i) for (c, i, _, __) in curr_map.keys()}
    for (company_name, item_name), prev_amt in prev_map.items():
        if (company_name, item_name) not in curr_keys:
            # item 정보 찾기
            item = (
                db.query(models.Item)
                .filter(
                    (models.Item.report_name == item_name) | (models.Item.name == item_name)
                )
                .first()
            )
            category = item.category if item else models.CategoryEnum.waste
            row = schemas.ReportRow(
                company_name=company_name,
                item_name=item_name,
                unit_price=0,
                current_quantity=0,
                current_amount=0,
                prev_amount=prev_amt,
            )
            if category == models.CategoryEnum.byproduct:
                byproducts.append(row)
            else:
                wastes.append(row)

    total_curr_by = sum(r.current_amount for r in byproducts)
    total_prev_by = sum(r.prev_amount for r in byproducts)
    total_curr_ws = sum(r.current_amount for r in wastes)
    total_prev_ws = sum(r.prev_amount for r in wastes)

    # 전월 수량 (EA 품목은 kg_per_unit 환산 적용)
    prev_by_qty = sum(
        tx.quantity * (tx.item.kg_per_unit or 1.0) for tx in prev_txs
        if tx.item.category == models.CategoryEnum.byproduct
    )
    prev_ws_qty = sum(
        tx.quantity * (tx.item.kg_per_unit or 1.0) for tx in prev_txs
        if tx.item.category == models.CategoryEnum.waste
    )

    # YTD (당해연도 1월 ~ 당월 누계/평균)
    ytd_by, ytd_ws = 0.0, 0.0
    for m in range(1, month + 1):
        for tx in _query_month(year, m):
            if tx.item.category == models.CategoryEnum.byproduct:
                ytd_by += tx.total_amount
            else:
                ytd_ws += tx.total_amount
    ytd_avg_by = ytd_by / month
    ytd_avg_ws = ytd_ws / month

    # 전년도 월평균: 2025는 원본 Excel 고정값, 이후 연도는 DB에서 계산
    _FIXED_2025 = {'byproduct': 11_253_267.0, 'waste': -7_840_358.0}
    prev_year = year - 1
    if prev_year == 2025:
        prev_year_avg_by = _FIXED_2025['byproduct']
        prev_year_avg_ws = _FIXED_2025['waste']
    else:
        py_by, py_ws = 0.0, 0.0
        for m in range(1, 13):
            for tx in _query_month(prev_year, m):
                if tx.item.category == models.CategoryEnum.byproduct:
                    py_by += tx.total_amount
                else:
                    py_ws += tx.total_amount
        prev_year_avg_by = py_by / 12
        prev_year_avg_ws = py_ws / 12

    return schemas.MonthlySummary(
        year=year,
        month=month,
        byproducts=byproducts,
        wastes=wastes,
        total_current_byproduct=total_curr_by,
        total_prev_byproduct=total_prev_by,
        total_current_waste=total_curr_ws,
        total_prev_waste=total_prev_ws,
        total_prev_byproduct_qty=prev_by_qty,
        total_prev_waste_qty=prev_ws_qty,
        ytd_cum_byproduct=ytd_by,
        ytd_cum_waste=ytd_ws,
        ytd_avg_byproduct=ytd_avg_by,
        ytd_avg_waste=ytd_avg_ws,
        prev_year_avg_byproduct=prev_year_avg_by,
        prev_year_avg_waste=prev_year_avg_ws,
    )


def get_annual_rows(
    year: int,
    company_id: Optional[int],
    item_id: Optional[int],
    db: Session,
) -> List[schemas.AnnualRow]:
    q = (
        db.query(models.Transaction)
        .options(
            joinedload(models.Transaction.item),
            joinedload(models.Transaction.company),
        )
        .filter(extract("year", models.Transaction.date) == year)
    )
    if company_id:
        q = q.filter(models.Transaction.company_id == company_id)
    if item_id:
        q = q.filter(models.Transaction.item_id == item_id)
    txs = q.order_by(models.Transaction.date).all()

    return [
        schemas.AnnualRow(
            date=tx.date,
            item_name=tx.item.name,
            company_name=tx.company.name,
            quantity=tx.quantity,
            unit_price=tx.unit_price,
            total_amount=tx.total_amount,
            note=tx.note,
        )
        for tx in txs
    ]
