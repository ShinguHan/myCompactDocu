from sqlalchemy.orm import Session
from models import Transaction, Company, Item, ReportMapping
from sqlalchemy import extract
import pandas as pd

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def sync_mappings(self):
        """
        Ensures all unique company/item pairs from transactions exist in report_mappings.
        """
        # Get all unique transaction pairs
        unique_tx_query = self.db.query(
            Company.name.label("raw_company"),
            Item.name.label("raw_item")
        ).select_from(Transaction).join(Company).join(Item).distinct()
        
        # Get all existing mappings
        existing_mappings = self.db.query(ReportMapping.raw_company, ReportMapping.raw_item).all()
        existing_set = set((m.raw_company, m.raw_item) for m in existing_mappings)
        
        new_mappings = []
        for tx in unique_tx_query.all():
            if (tx.raw_company, tx.raw_item) not in existing_set:
                new_mappings.append(ReportMapping(
                    raw_company=tx.raw_company,
                    raw_item=tx.raw_item,
                    standard_company=tx.raw_company, # Default to raw
                    standard_item=tx.raw_item,       # Default to raw
                    category='Unknown'
                ))
                existing_set.add((tx.raw_company, tx.raw_item))
        
        if new_mappings:
            self.db.add_all(new_mappings)
            self.db.commit()
            return len(new_mappings)
        return 0

    def generate_monthly_summary(self, year: int, month: int) -> pd.DataFrame:
        """
        Generates the monthly summary report.
        """
        # 1. Sync Missing Mappings
        self.sync_mappings()

        # 2. Fetch Transactions
        query = self.db.query(
            Transaction.date,
            Company.name.label("raw_company"),
            Item.name.label("raw_item"),
            Transaction.quantity,
            Transaction.total_amount
        ).join(Company).join(Item).filter(
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month
        )
        
        transactions_df = pd.read_sql(query.statement, self.db.bind)
        
        if transactions_df.empty:
            return pd.DataFrame()
            
        # 3. Fetch Mappings
        mappings_query = self.db.query(ReportMapping)
        mappings_df = pd.read_sql(mappings_query.statement, self.db.bind)
        
        # 4. Apply Mappings
        # Left join transactions with mappings on raw_company and raw_item
        merged_df = pd.merge(
            transactions_df, 
            mappings_df, 
            how='left', 
            left_on=['raw_item', 'raw_company'], 
            right_on=['raw_item', 'raw_company']
        )
        
        # Fill NaN standard names with raw names (fallback)
        merged_df['standard_item'] = merged_df['standard_item'].fillna(merged_df['raw_item'])
        merged_df['standard_company'] = merged_df['standard_company'].fillna(merged_df['raw_company'])
        merged_df['category'] = merged_df['category'].fillna('Unknown')
        
        # 5. Aggregate
        summary_df = merged_df.groupby(['category', 'standard_company', 'standard_item']).agg({
            'quantity': 'sum',
            'total_amount': 'sum'
        }).reset_index()
        
        # Rename columns for display
        summary_df.columns = ['Category', 'Company', 'Item', 'Total Quantity', 'Total Amount']
        
        return summary_df
