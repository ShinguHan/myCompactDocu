from sqlalchemy.orm import Session
from models import Transaction, Company, Item, ReportMapping
from sqlalchemy import extract
import pandas as pd

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def _read_sql(self, query):
        """SQLAlchemy 2.0 compatible pd.read_sql helper."""
        with self.db.get_bind().connect() as conn:
            return pd.read_sql(query.statement, conn)

    def sync_mappings(self):
        """
        Ensures all unique company/item pairs from transactions exist in report_mappings.
        """
        unique_tx_query = self.db.query(
            Company.name.label("raw_company"),
            Item.name.label("raw_item")
        ).select_from(Transaction).join(Company).join(Item).distinct()

        existing_mappings = self.db.query(ReportMapping.raw_company, ReportMapping.raw_item).all()
        existing_set = set((m.raw_company, m.raw_item) for m in existing_mappings)

        new_mappings = []
        for tx in unique_tx_query.all():
            if (tx.raw_company, tx.raw_item) not in existing_set:
                new_mappings.append(ReportMapping(
                    raw_company=tx.raw_company,
                    raw_item=tx.raw_item,
                    standard_company=tx.raw_company,
                    standard_item=tx.raw_item,
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
        Generates the monthly summary report with previous month comparison.
        """
        self.sync_mappings()

        if month == 1:
            prev_year = year - 1
            prev_month = 12
        else:
            prev_year = year
            prev_month = month - 1

        query_curr = self.db.query(
            Transaction.date,
            Company.name.label("raw_company"),
            Item.name.label("raw_item"),
            Transaction.quantity,
            Transaction.total_amount
        ).select_from(Transaction).join(Company).join(Item).filter(
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month
        )
        df_curr = self._read_sql(query_curr)

        query_prev = self.db.query(
            Company.name.label("raw_company"),
            Item.name.label("raw_item"),
            Transaction.total_amount
        ).select_from(Transaction).join(Company).join(Item).filter(
            extract('year', Transaction.date) == prev_year,
            extract('month', Transaction.date) == prev_month
        )
        df_prev = self._read_sql(query_prev)

        if df_curr.empty and df_prev.empty:
            return pd.DataFrame()

        mappings_df = self._read_sql(self.db.query(ReportMapping))

        if not df_curr.empty:
            merged_curr = pd.merge(
                df_curr, mappings_df,
                how='left',
                on=['raw_item', 'raw_company']
            )
            merged_curr['standard_item'] = merged_curr['standard_item'].fillna(merged_curr['raw_item'])
            merged_curr['standard_company'] = merged_curr['standard_company'].fillna(merged_curr['raw_company'])
            merged_curr['category'] = merged_curr['category'].fillna('Unknown')

            agg_curr = merged_curr.groupby(['category', 'standard_company', 'standard_item']).agg(
                curr_qty=('quantity', 'sum'),
                curr_amt=('total_amount', 'sum')
            ).reset_index()
        else:
            agg_curr = pd.DataFrame(columns=['category', 'standard_company', 'standard_item', 'curr_qty', 'curr_amt'])

        if not df_prev.empty:
            merged_prev = pd.merge(
                df_prev, mappings_df,
                how='left',
                on=['raw_item', 'raw_company']
            )
            merged_prev['standard_item'] = merged_prev['standard_item'].fillna(merged_prev['raw_item'])
            merged_prev['standard_company'] = merged_prev['standard_company'].fillna(merged_prev['raw_company'])
            merged_prev['category'] = merged_prev['category'].fillna('Unknown')

            agg_prev = merged_prev.groupby(['category', 'standard_company', 'standard_item']).agg(
                prev_amt=('total_amount', 'sum')
            ).reset_index()
        else:
            agg_prev = pd.DataFrame(columns=['category', 'standard_company', 'standard_item', 'prev_amt'])

        final_df = pd.merge(
            agg_curr, agg_prev,
            how='outer',
            on=['category', 'standard_company', 'standard_item']
        ).fillna(0)

        final_df['unit_price'] = final_df.apply(
            lambda x: x['curr_amt'] / x['curr_qty'] if x['curr_qty'] > 0 else 0, axis=1
        )
        final_df['note'] = ''

        final_df = final_df[['category', 'standard_company', 'standard_item', 'unit_price', 'curr_qty', 'curr_amt', 'prev_amt', 'note']]
        final_df.columns = ['Category', 'Company', 'Item', 'Unit Price', 'Current Qty', 'Current Amount', 'Previous Amount', 'Note']

        return final_df

    def get_grouped_transactions(self, start_date, end_date):
        """
        Fetches transactions within a date range, grouped by Date and Company.
        """
        query = self.db.query(
            Transaction.date,
            Company.name.label("company_name"),
            Item.name.label("item_name"),
            Transaction.quantity,
            Transaction.total_amount
        ).join(Company).join(Item).filter(
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).order_by(Transaction.date, Company.name)

        rows = query.all()

        grouped = {}
        for row in rows:
            key = (row.date, row.company_name)
            if key not in grouped:
                grouped[key] = {
                    'date': row.date,
                    'company_name': row.company_name,
                    'items': []
                }
            grouped[key]['items'].append({
                'name': row.item_name,
                'quantity': row.quantity,
                'amount': row.total_amount
            })

        return list(grouped.values())
