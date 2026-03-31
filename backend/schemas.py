from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date as date_, datetime
from enum import Enum


class CategoryEnum(str, Enum):
    byproduct = "부산물"
    waste = "폐기물"


class UnitTypeEnum(str, Enum):
    per_unit = "per_unit"
    fixed = "fixed"


# ── Item ──────────────────────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    name: str
    report_name: Optional[str] = None
    unit: str = "원/kg"
    category: CategoryEnum
    kg_per_unit: Optional[float] = None


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    report_name: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[CategoryEnum] = None
    kg_per_unit: Optional[float] = None


class ItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    report_name: Optional[str]
    unit: str
    category: CategoryEnum
    kg_per_unit: Optional[float] = None


# ── Company ───────────────────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str


class CompanyUpdate(BaseModel):
    name: str


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


# ── ItemCompany ───────────────────────────────────────────────────────────────

class ItemCompanyCreate(BaseModel):
    item_id: int
    company_id: int
    sort_order: int = 1


class ItemCompanyUpdate(BaseModel):
    sort_order: int


class ItemCompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_id: int
    company_id: int
    sort_order: int
    item: ItemRead
    company: CompanyRead


# ── Contract ──────────────────────────────────────────────────────────────────

class ContractCreate(BaseModel):
    item_id: int
    company_id: int
    unit_price: float
    unit_type: UnitTypeEnum = UnitTypeEnum.per_unit
    effective_date: date_
    note: Optional[str] = None


class ContractUpdate(BaseModel):
    unit_price: Optional[float] = None
    unit_type: Optional[UnitTypeEnum] = None
    effective_date: Optional[date_] = None
    note: Optional[str] = None


class ContractRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_id: int
    company_id: int
    unit_price: float
    unit_type: UnitTypeEnum
    effective_date: date_
    note: Optional[str]
    item: ItemRead
    company: CompanyRead


# ── Transaction ───────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    date: date_
    item_id: int
    company_id: int
    quantity: float
    unit_price: float
    total_amount: float
    note: Optional[str] = None


class TransactionUpdate(BaseModel):
    date: Optional[date_] = None
    item_id: Optional[int] = None
    company_id: Optional[int] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None
    note: Optional[str] = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: date_
    item_id: int
    company_id: int
    quantity: float
    unit_price: float
    total_amount: float
    note: Optional[str]
    item: ItemRead
    company: CompanyRead


class TransactionBatchCreate(BaseModel):
    transactions: List[TransactionCreate]


# ── ExitPass ──────────────────────────────────────────────────────────────────

class ExitPassCreate(BaseModel):
    date: date_
    company_id: int
    transaction_ids: List[int]


class ExitPassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: date_
    company_id: int
    photo_path: Optional[str]
    created_at: datetime
    company: CompanyRead
    transactions: List["ExitPassTransactionRead"]


class ExitPassTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    exit_pass_id: int
    transaction_id: int
    transaction: TransactionRead


ExitPassRead.model_rebuild()


# ── Report ────────────────────────────────────────────────────────────────────

class ReportRow(BaseModel):
    company_name: str
    item_name: str
    unit_price: float
    current_quantity: float
    current_amount: float
    prev_amount: float
    note: Optional[str] = None


class MonthlySummary(BaseModel):
    year: int
    month: int
    byproducts: List[ReportRow]
    wastes: List[ReportRow]
    total_current_byproduct: float
    total_prev_byproduct: float
    total_current_waste: float
    total_prev_waste: float
    # 전월 수량
    total_prev_byproduct_qty: float = 0.0
    total_prev_waste_qty: float = 0.0
    # 2026 YTD (당월 포함 누계 / 평균)
    ytd_cum_byproduct: float = 0.0
    ytd_cum_waste: float = 0.0
    ytd_avg_byproduct: float = 0.0
    ytd_avg_waste: float = 0.0
    # 전년도 월평균 (2025는 고정값, 이후 연도는 DB 계산)
    prev_year_avg_byproduct: Optional[float] = None
    prev_year_avg_waste: Optional[float] = None


class AnnualRow(BaseModel):
    date: date_
    item_name: str
    company_name: str
    quantity: float
    unit_price: float
    total_amount: float
    note: Optional[str]


# ── Import Preview ────────────────────────────────────────────────────────────

class ImportPreviewRow(BaseModel):
    date: date_
    item_name: str
    company_name: str
    quantity: float
    unit_price: float
    total_amount: float
    note: Optional[str]
    is_duplicate: bool


class ImportPreview(BaseModel):
    new_count: int
    duplicate_count: int
    unknown_items: List[str]
    rows: List[ImportPreviewRow]
