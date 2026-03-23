from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models, schemas

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=List[schemas.CompanyRead])
def list_companies(db: Session = Depends(get_db)):
    return db.query(models.Company).order_by(models.Company.name).all()


@router.post("", response_model=schemas.CompanyRead, status_code=201)
def create_company(body: schemas.CompanyCreate, db: Session = Depends(get_db)):
    if db.query(models.Company).filter(models.Company.name == body.name).first():
        raise HTTPException(status_code=409, detail="이미 존재하는 업체명입니다")
    company = models.Company(**body.model_dump())
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.put("/{company_id}", response_model=schemas.CompanyRead)
def update_company(company_id: int, body: schemas.CompanyUpdate, db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="업체를 찾을 수 없습니다")
    company.name = body.name
    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=204)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="업체를 찾을 수 없습니다")
    db.delete(company)
    db.commit()
