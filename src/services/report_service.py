from sqlalchemy.orm import Session
from models import Transaction, Company, Item, ReportMapping
from sqlalchemy import extract
import pandas as pd

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def generate_monthly_summary(self, year: int, month: int) -> pd.DataFrame:
        """
        Generates the monthly summary report.
        """
        # 1. Fetch Transactions
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
            
        # 2. Fetch Mappings
        mappings_query = self.db.query(ReportMapping)
        mappings_df = pd.read_sql(mappings_query.statement, self.db.bind)
        
        # 3. Apply Mappings
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
        
        # 4. Aggregate
        summary_df = merged_df.groupby(['category', 'standard_company', 'standard_item']).agg({
            'quantity': 'sum',
            'total_amount': 'sum'
        }).reset_index()
        
        # Rename columns for display
        summary_df.columns = ['Category', 'Company', 'Item', 'Total Quantity', 'Total Amount']
        
        return summary_df
