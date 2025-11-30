from sqlalchemy.orm import Session
from models import Contract
from sqlalchemy import desc
import datetime

class ContractService:
    def __init__(self, db: Session):
        self.db = db

    def get_contract(self, company_id: int, item_id: int, date: datetime.date):
        """
        Fetch the most recent contract effective on or before the given date.
        """
        return self.db.query(Contract).filter(
            Contract.company_id == company_id,
            Contract.item_id == item_id,
            Contract.effective_date <= date
        ).order_by(desc(Contract.effective_date)).first()

    def create_contract(self, company_id: int, item_id: int, unit_price: float = None, fixed_total: float = None, effective_date: datetime.date = None):
        """
        Create a new contract.
        """
        if effective_date is None:
            effective_date = datetime.date.today()
            
        contract = Contract(
            company_id=company_id,
            item_id=item_id,
            unit_price=unit_price,
            fixed_total_amount=fixed_total,
            effective_date=effective_date
        )
        self.db.add(contract)
        self.db.commit()
        return contract
