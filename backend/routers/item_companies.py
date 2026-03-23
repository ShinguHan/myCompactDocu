from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from database import get_db
import models, schemas

router = APIRouter(prefix="/api/item-companies", tags=["item-companies"])


@router.get("", response_model=List[schemas.ItemCompanyRead])
def list_item_companies(
    item_id: Optional[int] = None,
    company_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.ItemCompany).options(
        joinedload(models.ItemCompany.item),
        joinedload(models.ItemCompany.company),
    )
    if item_id:
        q = q.filter(models.ItemCompany.item_id == item_id)
    if company_id:
        q = q.filter(models.ItemCompany.company_id == company_id)
    return q.order_by(models.ItemCompany.item_id, models.ItemCompany.sort_order).all()


@router.post("", response_model=schemas.ItemCompanyRead, status_code=201)
def create_link(body: schemas.ItemCompanyCreate, db: Session = Depends(get_db)):
    exists = db.query(models.ItemCompany).filter(
        models.ItemCompany.item_id == body.item_id,
        models.ItemCompany.company_id == body.company_id,
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="이미 연결된 품목-업체입니다")
    link = models.ItemCompany(**body.model_dump())
    db.add(link)
    db.commit()
    db.refresh(link)
    return db.query(models.ItemCompany).options(
        joinedload(models.ItemCompany.item),
        joinedload(models.ItemCompany.company),
    ).filter(models.ItemCompany.id == link.id).first()


@router.put("/{link_id}", response_model=schemas.ItemCompanyRead)
def update_link(link_id: int, body: schemas.ItemCompanyUpdate, db: Session = Depends(get_db)):
    link = db.query(models.ItemCompany).filter(models.ItemCompany.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="연결을 찾을 수 없습니다")
    link.sort_order = body.sort_order
    db.commit()
    return db.query(models.ItemCompany).options(
        joinedload(models.ItemCompany.item),
        joinedload(models.ItemCompany.company),
    ).filter(models.ItemCompany.id == link_id).first()


@router.delete("/{link_id}", status_code=204)
def delete_link(link_id: int, db: Session = Depends(get_db)):
    link = db.query(models.ItemCompany).filter(models.ItemCompany.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="연결을 찾을 수 없습니다")
    db.delete(link)
    db.commit()
