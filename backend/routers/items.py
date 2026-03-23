from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
import models, schemas

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("", response_model=List[schemas.ItemRead])
def list_items(category: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(models.Item)
    if category:
        q = q.filter(models.Item.category == category)
    return q.order_by(models.Item.name).all()


@router.post("", response_model=schemas.ItemRead, status_code=201)
def create_item(body: schemas.ItemCreate, db: Session = Depends(get_db)):
    if db.query(models.Item).filter(models.Item.name == body.name).first():
        raise HTTPException(status_code=409, detail="이미 존재하는 품목명입니다")
    item = models.Item(**body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=schemas.ItemRead)
def update_item(item_id: int, body: schemas.ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없습니다")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="품목을 찾을 수 없습니다")
    db.delete(item)
    db.commit()
