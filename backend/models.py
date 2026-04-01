from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from database import Base


class CategoryEnum(str, enum.Enum):
    byproduct = "부산물"
    waste = "폐기물"


class UnitTypeEnum(str, enum.Enum):
    per_unit = "per_unit"   # unit_price × quantity
    fixed = "fixed"         # unit_price = 총액 고정


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)          # 입출고대장 표기명
    report_name = Column(String, nullable=True)                 # 보고서 표기명 (다를 경우)
    unit = Column(String, nullable=False, default="원/kg")      # 원/kg, 원/EA, 원/대
    category = Column(Enum(CategoryEnum), nullable=False)
    kg_per_unit = Column(Float, nullable=True)                  # EA→kg 환산계수 (예: 200L드럼=20)

    companies = relationship("ItemCompany", back_populates="item", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="item", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="item")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    items = relationship("ItemCompany", back_populates="company", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="company", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="company")
    exit_passes = relationship("ExitPass", back_populates="company")


class ItemCompany(Base):
    """품목-업체 연결 (목록표의 처리업체1~4)"""
    __tablename__ = "item_companies"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    sort_order = Column(Integer, nullable=False, default=1)     # 처리업체 순서

    item = relationship("Item", back_populates="companies")
    company = relationship("Company", back_populates="items")


class Contract(Base):
    """계약단가"""
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    unit_price = Column(Float, nullable=False)
    unit_type = Column(Enum(UnitTypeEnum), nullable=False, default=UnitTypeEnum.per_unit)
    effective_date = Column(Date, nullable=False)
    note = Column(String, nullable=True)

    item = relationship("Item", back_populates="contracts")
    company = relationship("Company", back_populates="contracts")


class Transaction(Base):
    """폐기물, 부산물 입출고대장"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    vehicle_count = Column(Integer, nullable=True)   # 폐목재_MDF: 차량 대수 기반 정산
    note = Column(Text, nullable=True)

    item = relationship("Item", back_populates="transactions")
    company = relationship("Company", back_populates="transactions")
    exit_pass_links = relationship("ExitPassTransaction", back_populates="transaction", cascade="all, delete-orphan")


class ExitPass(Base):
    """반출증"""
    __tablename__ = "exit_passes"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    photo_path = Column(String, nullable=True)      # 업로드한 반출 사진
    created_at = Column(DateTime, server_default=func.now())

    company = relationship("Company", back_populates="exit_passes")
    transactions = relationship("ExitPassTransaction", back_populates="exit_pass", cascade="all, delete-orphan")


class ExitPassTransaction(Base):
    """반출증-거래 연결"""
    __tablename__ = "exit_pass_transactions"

    id = Column(Integer, primary_key=True, index=True)
    exit_pass_id = Column(Integer, ForeignKey("exit_passes.id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)

    exit_pass = relationship("ExitPass", back_populates="transactions")
    transaction = relationship("Transaction", back_populates="exit_pass_links")
