from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
import datetime
from sqlalchemy.orm import relationship
from database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    transactions = relationship("Transaction", back_populates="company")

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    transactions = relationship("Transaction", back_populates="item")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Float) # Weight or Count
    unit_price = Column(Float)
    total_amount = Column(Float)
    note = Column(Text, nullable=True)

    company = relationship("Company", back_populates="transactions")
    item = relationship("Item", back_populates="transactions")

class ImportHistory(Base):
    __tablename__ = "import_history"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    upload_date = Column(Date, default=datetime.datetime.now)
    success_count = Column(Integer)
    duplicate_count = Column(Integer)

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    unit_price = Column(Float, nullable=True)
    fixed_total_amount = Column(Float, nullable=True)
    effective_date = Column(Date, default=datetime.date.today)

    company = relationship("Company")
    item = relationship("Item")

class ReportMapping(Base):
    __tablename__ = "report_mappings"

    id = Column(Integer, primary_key=True, index=True)
    raw_item = Column(String, index=True)
    raw_company = Column(String, index=True)
    standard_item = Column(String)
    standard_company = Column(String)
    category = Column(String, nullable=True) # '부산물' or '폐기물'

