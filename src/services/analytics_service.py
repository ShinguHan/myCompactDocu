from sqlalchemy.orm import Session, joinedload
from models import Transaction, Company, Item
import pandas as pd

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_companies(self):
        return self.db.query(Company).all()

    def get_items(self):
        return self.db.query(Item).all()

    def get_filtered_transactions(self, company_name: str = "All", item_name: str = "All") -> pd.DataFrame:
        """
        Fetch transactions filtered by company and item.
        Returns a DataFrame suitable for the dashboard.
        """
        query = self.db.query(Transaction).options(joinedload(Transaction.company), joinedload(Transaction.item))

        if company_name != "All":
            query = query.join(Company).filter(Company.name == company_name)

        if item_name != "All":
            query = query.join(Item).filter(Item.name == item_name)

        transactions = query.order_by(Transaction.date.desc()).all()

        if not transactions:
            return pd.DataFrame()

        data = []
        for t in transactions:
            data.append({
                "Date": t.date,
                "Company": t.company.name,
                "Item": t.item.name,
                "Quantity": t.quantity,
                "Unit Price": t.unit_price,
                "Total Amount": t.total_amount,
                "Note": t.note
            })
        
        return pd.DataFrame(data)
