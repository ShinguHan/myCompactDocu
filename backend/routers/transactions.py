from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from datetime import date
import io

from database import get_db
import models, schemas
from services.import_service import parse_excel_preview, confirm_import

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _with_relations(q):
    return q.options(
        joinedload(models.Transaction.item),
        joinedload(models.Transaction.company),
    )


def _next_ledger_number(db: Session) -> int:
    latest = (
        db.query(models.Transaction)
        .filter(models.Transaction.ledger_number.is_not(None))
        .order_by(models.Transaction.ledger_number.desc(), models.Transaction.id.desc())
        .first()
    )
    return (latest.ledger_number if latest and latest.ledger_number is not None else 0) + 1


def _assign_missing_ledger_numbers(rows, db: Session) -> None:
    next_ledger = _next_ledger_number(db)
    for row in rows:
        if row.ledger_number is None:
            row.ledger_number = next_ledger
            next_ledger += 1


@router.get("", response_model=List[schemas.TransactionRead])
def list_transactions(
    start: Optional[date] = None,
    end: Optional[date] = None,
    company_id: Optional[int] = None,
    item_id: Optional[int] = None,
    page: int = 1,
    size: int = 100,
    db: Session = Depends(get_db),
):
    q = _with_relations(db.query(models.Transaction))
    if start:
        q = q.filter(models.Transaction.date >= start)
    if end:
        q = q.filter(models.Transaction.date <= end)
    if company_id:
        q = q.filter(models.Transaction.company_id == company_id)
    if item_id:
        q = q.filter(models.Transaction.item_id == item_id)
    q = q.order_by(models.Transaction.date.desc())
    offset = (page - 1) * size
    return q.offset(offset).limit(size).all()


@router.get("/grouped")
def list_grouped(
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    """날짜+업체 그룹별 트랜잭션 목록 (반출증 선택용)"""
    q = _with_relations(db.query(models.Transaction))
    if start:
        q = q.filter(models.Transaction.date >= start)
    if end:
        q = q.filter(models.Transaction.date <= end)
    txs = q.order_by(models.Transaction.date.desc(), models.Transaction.company_id).all()

    groups = {}
    for tx in txs:
        key = f"{tx.date}_{tx.company_id}"
        if key not in groups:
            groups[key] = {
                "date": str(tx.date),
                "company_id": tx.company_id,
                "company_name": tx.company.name,
                "transactions": [],
            }
        groups[key]["transactions"].append({
            "id": tx.id,
            "item_name": tx.item.name,
            "quantity": tx.quantity,
            "unit_price": tx.unit_price,
            "total_amount": tx.total_amount,
            "note": tx.note,
        })
    return list(groups.values())


@router.post("", response_model=schemas.TransactionRead, status_code=201)
def create_transaction(body: schemas.TransactionCreate, db: Session = Depends(get_db)):
    data = body.model_dump()
    if data.get("ledger_number") is None:
        data["ledger_number"] = _next_ledger_number(db)
    tx = models.Transaction(**data)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return _with_relations(db.query(models.Transaction)).filter(models.Transaction.id == tx.id).first()


@router.post("/batch", response_model=List[schemas.TransactionRead], status_code=201)
def batch_create(body: schemas.TransactionBatchCreate, db: Session = Depends(get_db)):
    txs = []
    for t in body.transactions:
        data = t.model_dump()
        txs.append(models.Transaction(**data))
    _assign_missing_ledger_numbers(txs, db)
    db.add_all(txs)
    db.commit()
    ids = [tx.id for tx in txs]
    return _with_relations(db.query(models.Transaction)).filter(
        models.Transaction.id.in_(ids)
    ).all()


@router.put("/{tx_id}", response_model=schemas.TransactionRead)
def update_transaction(tx_id: int, body: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")

    new_ledger = body.ledger_number  # None이면 변경 없음
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(tx, k, v)

    # 관리대장 번호가 지정된 경우: 이후 거래에 자동 증가 적용
    if new_ledger is not None:
        subsequent = (
            db.query(models.Transaction)
            .filter(
                (models.Transaction.date > tx.date) |
                (and_(models.Transaction.date == tx.date,
                      models.Transaction.id > tx_id))
            )
            .order_by(models.Transaction.date.asc(), models.Transaction.id.asc())
            .all()
        )
        for i, t in enumerate(subsequent, start=1):
            t.ledger_number = new_ledger + i

    db.commit()
    return _with_relations(db.query(models.Transaction)).filter(models.Transaction.id == tx_id).first()


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="거래를 찾을 수 없습니다")
    db.delete(tx)
    db.commit()


@router.post("/import/preview", response_model=schemas.ImportPreview)
async def import_preview(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """엑셀 파일 파싱 후 미리보기 (dry-run)"""
    content = await file.read()
    return parse_excel_preview(io.BytesIO(content), db)


@router.post("/import/confirm", response_model=List[schemas.TransactionRead])
def import_confirm(rows: List[schemas.TransactionCreate], db: Session = Depends(get_db)):
    """미리보기 확인 후 실제 저장"""
    return confirm_import(rows, db)
