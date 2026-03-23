from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import date

from database import get_db
import models, schemas

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.get("", response_model=List[schemas.ContractRead])
def list_contracts(
    item_id: Optional[int] = None,
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Contract).options(
        joinedload(models.Contract.item),
        joinedload(models.Contract.company),
    )
    if item_id:
        q = q.filter(models.Contract.item_id == item_id)
    if company_id:
        q = q.filter(models.Contract.company_id == company_id)
    return q.order_by(models.Contract.effective_date.desc()).all()


@router.get("/active", response_model=Optional[schemas.ContractRead])
def get_active_contract(
    item_id: int,
    company_id: int,
    on_date: date = None,
    db: Session = Depends(get_db),
):
    """특정 날짜 기준 유효한 계약단가 조회"""
    check_date = on_date or date.today()
    contract = (
        db.query(models.Contract)
        .options(joinedload(models.Contract.item), joinedload(models.Contract.company))
        .filter(
            models.Contract.item_id == item_id,
            models.Contract.company_id == company_id,
            models.Contract.effective_date <= check_date,
        )
        .order_by(models.Contract.effective_date.desc())
        .first()
    )
    return contract


@router.post("", response_model=schemas.ContractRead, status_code=201)
def create_contract(body: schemas.ContractCreate, db: Session = Depends(get_db)):
    contract = models.Contract(**body.model_dump())
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return db.query(models.Contract).options(
        joinedload(models.Contract.item),
        joinedload(models.Contract.company),
    ).filter(models.Contract.id == contract.id).first()


@router.put("/{contract_id}", response_model=schemas.ContractRead)
def update_contract(contract_id: int, body: schemas.ContractUpdate, db: Session = Depends(get_db)):
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(contract, k, v)
    db.commit()
    return db.query(models.Contract).options(
        joinedload(models.Contract.item),
        joinedload(models.Contract.company),
    ).filter(models.Contract.id == contract_id).first()


@router.delete("/{contract_id}", status_code=204)
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(models.Contract).filter(models.Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="계약을 찾을 수 없습니다")
    db.delete(contract)
    db.commit()
