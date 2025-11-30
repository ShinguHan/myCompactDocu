from sqlalchemy.orm import Session
from models import Transaction, Company, Item, ImportHistory
from sqlalchemy import func
import pandas as pd

class TransactionService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_transactions_df(self) -> pd.DataFrame:
        """Fetch all transactions as a DataFrame with Company and Item names."""
        query = self.db.query(
            Transaction.id,
            Transaction.date,
            Company.name.label("company"),
            Item.name.label("item"),
            Transaction.quantity,
            Transaction.unit_price,
            Transaction.total_amount,
            Transaction.note
        ).join(Company).join(Item).order_by(Transaction.date.desc())
        
        return pd.read_sql(query.statement, self.db.bind)

    def update_transaction(self, tx_id: int, data: dict):
        """Update a single transaction."""
        self.db.query(Transaction).filter(Transaction.id == tx_id).update(data)
        self.db.commit()

    def delete_duplicates(self) -> int:
        """
        Deletes duplicate transactions, keeping the one with the smallest ID.
        Returns the number of deleted records.
        """
        # Subquery to find min IDs for each group
        subquery = self.db.query(func.min(Transaction.id)).group_by(
            Transaction.date,
            Transaction.company_id,
            Transaction.item_id,
            Transaction.quantity,
            Transaction.unit_price
        )
        
        keep_ids = [r[0] for r in subquery.all()]
        
        if not keep_ids:
            return 0
            
        delete_q = self.db.query(Transaction).filter(Transaction.id.notin_(keep_ids))
        deleted_count = delete_q.delete(synchronize_session=False)
        self.db.commit()
        return deleted_count

    def create_transaction(self, data: dict):
        """
        Create a new transaction.
        Handles creation of Company and Item if they don't exist.
        """
        company_name = data['company_name']
        item_name = data['item_name']
        
        # Get or Create Company
        company = self.db.query(Company).filter(Company.name == company_name).first()
        if not company:
            company = Company(name=company_name)
            self.db.add(company)
            self.db.commit()
            self.db.refresh(company)
            
        # Get or Create Item
        item = self.db.query(Item).filter(Item.name == item_name).first()
        if not item:
            item = Item(name=item_name)
            self.db.add(item)
            self.db.commit()
            self.db.refresh(item)
            
        # Create Transaction
        transaction = Transaction(
            date=data['date'],
            company_id=company.id,
            item_id=item.id,
            quantity=data['quantity'],
            unit_price=data['unit_price'],
            total_amount=data['total_amount'],
            note=data.get('note', '')
        )
        self.db.add(transaction)
        self.db.commit()

    def get_import_history_df(self) -> pd.DataFrame:
        """Fetch import history as a DataFrame."""
        return pd.read_sql(self.db.query(ImportHistory).statement, self.db.bind)
