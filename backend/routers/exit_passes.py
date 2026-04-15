import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date

from database import get_db
import models, schemas
from services.print_service import generate_exit_pass

router = APIRouter(prefix="/api/exit-passes", tags=["exit-passes"])

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "images")
os.makedirs(IMAGES_DIR, exist_ok=True)


def _load_full(exit_pass_id: int, db: Session):
    return (
        db.query(models.ExitPass)
        .options(
            joinedload(models.ExitPass.company),
            joinedload(models.ExitPass.transactions).joinedload(
                models.ExitPassTransaction.transaction
            ).joinedload(models.Transaction.item),
            joinedload(models.ExitPass.transactions).joinedload(
                models.ExitPassTransaction.transaction
            ).joinedload(models.Transaction.company),
        )
        .filter(models.ExitPass.id == exit_pass_id)
        .first()
    )


def _next_exit_pass_number(db: Session) -> int:
    latest = (
        db.query(models.ExitPass)
        .order_by(models.ExitPass.number.desc(), models.ExitPass.id.desc())
        .first()
    )
    return (latest.number if latest else 0) + 1


def _renumber_ledger_groups(db: Session) -> None:
    """관리대장 번호를 날짜/등록순으로 다시 매긴다.

    같은 반출증에 묶인 거래들은 하나의 관리대장 번호를 공유한다.
    """
    txs = (
        db.query(models.Transaction)
        .options(
            joinedload(models.Transaction.exit_pass_links).joinedload(
                models.ExitPassTransaction.exit_pass
            )
        )
        .order_by(models.Transaction.date.asc(), models.Transaction.id.asc())
        .all()
    )
    existing_numbers = [tx.ledger_number for tx in txs if tx.ledger_number is not None]
    group_numbers = {}
    next_number = min(existing_numbers) if existing_numbers else 1

    for tx in txs:
        exit_pass_ids = sorted(
            link.exit_pass_id for link in tx.exit_pass_links if link.exit_pass_id
        )
        group_key = (
            ("exit_pass", exit_pass_ids[0]) if exit_pass_ids else ("transaction", tx.id)
        )
        if group_key not in group_numbers:
            group_numbers[group_key] = next_number
            next_number += 1
        tx.ledger_number = group_numbers[group_key]


@router.get("", response_model=List[schemas.ExitPassRead])
def list_exit_passes(
    company_id: Optional[int] = None,
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.ExitPass).options(
        joinedload(models.ExitPass.company),
        joinedload(models.ExitPass.transactions).joinedload(
            models.ExitPassTransaction.transaction
        ).joinedload(models.Transaction.item),
        joinedload(models.ExitPass.transactions).joinedload(
            models.ExitPassTransaction.transaction
        ).joinedload(models.Transaction.company),
    )
    if company_id:
        q = q.filter(models.ExitPass.company_id == company_id)
    if start:
        q = q.filter(models.ExitPass.date >= start)
    if end:
        q = q.filter(models.ExitPass.date <= end)
    return q.order_by(models.ExitPass.created_at.desc(), models.ExitPass.id.desc()).all()


@router.get("/{ep_id}", response_model=schemas.ExitPassRead)
def get_exit_pass(ep_id: int, db: Session = Depends(get_db)):
    ep = _load_full(ep_id, db)
    if not ep:
        raise HTTPException(status_code=404, detail="반출증을 찾을 수 없습니다")
    return ep


@router.post("", response_model=schemas.ExitPassRead, status_code=201)
def create_exit_pass(body: schemas.ExitPassCreate, db: Session = Depends(get_db)):
    transactions = []
    for tx_id in body.transaction_ids:
        tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
        if not tx:
            raise HTTPException(status_code=404, detail=f"거래 {tx_id}를 찾을 수 없습니다")
        transactions.append(tx)

    ep = models.ExitPass(
        number=_next_exit_pass_number(db),
        date=body.date,
        company_id=body.company_id,
    )
    db.add(ep)
    db.flush()

    old_links = (
        db.query(models.ExitPassTransaction)
        .filter(models.ExitPassTransaction.transaction_id.in_(body.transaction_ids))
        .all()
    )
    old_exit_pass_ids = {link.exit_pass_id for link in old_links}
    for link in old_links:
        db.delete(link)
    db.flush()

    for old_ep_id in old_exit_pass_ids:
        has_links = (
            db.query(models.ExitPassTransaction)
            .filter(models.ExitPassTransaction.exit_pass_id == old_ep_id)
            .first()
        )
        if not has_links:
            old_ep = db.query(models.ExitPass).filter(models.ExitPass.id == old_ep_id).first()
            if old_ep:
                db.delete(old_ep)

    existing_tx_ids = {
        link.transaction_id
        for link in db.query(models.ExitPassTransaction)
        .filter(models.ExitPassTransaction.exit_pass_id == ep.id)
        .all()
    }
    for tx in transactions:
        if tx.id in existing_tx_ids:
            continue
        link = models.ExitPassTransaction(exit_pass_id=ep.id, transaction_id=tx.id)
        db.add(link)

    db.flush()
    _renumber_ledger_groups(db)
    db.commit()
    return _load_full(ep.id, db)

@router.post("/{ep_id}/photo")
async def upload_photo(ep_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    ep = db.query(models.ExitPass).filter(models.ExitPass.id == ep_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="반출증을 찾을 수 없습니다")

    ext = os.path.splitext(file.filename)[1]
    filename = f"exitpass_{ep_id}{ext}"
    save_path = os.path.join(IMAGES_DIR, filename)

    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    ep.photo_path = save_path
    db.commit()
    return {"photo_path": save_path}


@router.get("/{ep_id}/download")
def download_exit_pass(ep_id: int, db: Session = Depends(get_db)):
    ep = _load_full(ep_id, db)
    if not ep:
        raise HTTPException(status_code=404, detail="반출증을 찾을 수 없습니다")

    output_path = generate_exit_pass(ep)
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"반출증_{ep.date}_{ep.company.name}.xlsx",
    )


@router.delete("/{ep_id}", status_code=204)
def delete_exit_pass(ep_id: int, db: Session = Depends(get_db)):
    ep = db.query(models.ExitPass).filter(models.ExitPass.id == ep_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="반출증을 찾을 수 없습니다")
    db.delete(ep)
    db.flush()
    _renumber_ledger_groups(db)
    db.commit()
