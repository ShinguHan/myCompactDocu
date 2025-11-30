import pandas as pd
import datetime
from sqlalchemy.orm import Session
from models import Company, Item, Transaction, ImportHistory
from .base import BaseImporter

class WasteImporter(BaseImporter):
    def parse(self, file_input) -> list:
        """
        Parses the Excel file and returns a list of transaction dictionaries.
        """
        xls = pd.ExcelFile(file_input)
        
        # Parse '연간처리 세부현황'
        sheet_name = '연간처리 세부현황'
        if sheet_name not in xls.sheet_names:
            raise ValueError(f"Sheet '{sheet_name}' not found. Available sheets: {xls.sheet_names}")
        
        # Read raw data to handle complex headers
        df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        
        item_row = df.iloc[1]
        company_row = df.iloc[2]
        type_row = df.iloc[3]
        
        transaction_groups = []
        
        for col_idx in range(len(df.columns)):
            col_type = str(type_row[col_idx]).strip()
            
            if col_type == '단가':
                item_name = item_row[col_idx]
                if pd.isna(item_name):
                    for prev in range(col_idx - 1, -1, -1):
                        if not pd.isna(item_row[prev]):
                            item_name = item_row[prev]
                            break
                
                company_name = company_row[col_idx]
                if pd.isna(company_name):
                     for prev in range(col_idx - 1, -1, -1):
                        if not pd.isna(company_row[prev]):
                            company_name = company_row[prev]
                            break
                
                # Clean names
                item_name = str(item_name).strip() if item_name else "Unknown Item"
                company_name = str(company_name).strip() if company_name else "Unknown Company"
                
                # Remove "업체:" prefix if present
                if company_name.startswith("업체:"):
                    company_name = company_name.replace("업체:", "").strip()

                transaction_groups.append({
                    'item': item_name,
                    'company': company_name,
                    'col_unit_price': col_idx,
                    'col_qty': col_idx + 1,
                    'col_amount': col_idx + 2
                })
                
        # Process Data Rows
        parsed_transactions = []
        
        for row_idx in range(4, len(df)):
            date_val = df.iloc[row_idx, 1] # Date is in column 1
            
            if pd.isna(date_val):
                continue
                
            # Check if it's a valid date
            if not isinstance(date_val, datetime.datetime):
                continue
                
            for group in transaction_groups:
                qty = df.iloc[row_idx, group['col_qty']]
                amount = df.iloc[row_idx, group['col_amount']]
                unit_price = df.iloc[row_idx, group['col_unit_price']]
                
                # Skip empty transactions
                if (pd.isna(qty) or qty == 0) and (pd.isna(amount) or amount == 0):
                    continue
                
                parsed_transactions.append({
                    'date': date_val.date(),
                    'company_name': group['company'],
                    'item_name': group['item'],
                    'quantity': float(qty) if not pd.isna(qty) else 0.0,
                    'unit_price': float(unit_price) if not pd.isna(unit_price) else 0.0,
                    'total_amount': float(amount) if not pd.isna(amount) else 0.0
                })
                
        return parsed_transactions

    def validate(self, data: list) -> list:
        # Validation logic if needed (e.g. check for negative values)
        return data

    def check_duplicates(self, transactions: list, db: Session) -> dict:
        """
        Checks for duplicates in the database.
        Returns a dictionary with 'new' and 'duplicates' lists.
        """
        new_tx = []
        duplicate_tx = []
        
        for tx in transactions:
            # Resolve Company ID
            company = db.query(Company).filter(Company.name == tx['company_name']).first()
            item = db.query(Item).filter(Item.name == tx['item_name']).first()
            
            is_dup = False
            if company and item:
                existing = db.query(Transaction).filter(
                    Transaction.date == tx['date'],
                    Transaction.company_id == company.id,
                    Transaction.item_id == item.id
                ).first()
                if existing:
                    is_dup = True
            
            if is_dup:
                duplicate_tx.append(tx)
            else:
                new_tx.append(tx)
                
        return {'new': new_tx, 'duplicates': duplicate_tx}

    def save(self, transactions: list, db: Session, filename: str, duplicate_count: int = 0) -> int:
        """
        Saves the list of transactions to the database.
        Handles creation of Company and Item if they don't exist.
        Logs the import to ImportHistory.
        """
        imported_count = 0
        
        for tx in transactions:
            # Get or Create Company
            company = db.query(Company).filter(Company.name == tx['company_name']).first()
            if not company:
                company = Company(name=tx['company_name'])
                db.add(company)
                db.commit()
                db.refresh(company)
                
            # Get or Create Item
            item = db.query(Item).filter(Item.name == tx['item_name']).first()
            if not item:
                item = Item(name=tx['item_name'])
                db.add(item)
                db.commit()
                db.refresh(item)
                
            # Create Transaction
            transaction = Transaction(
                date=tx['date'],
                company_id=company.id,
                item_id=item.id,
                quantity=tx['quantity'],
                unit_price=tx['unit_price'],
                total_amount=tx['total_amount']
            )
            db.add(transaction)
            imported_count += 1
            
        # Log to History
        history = ImportHistory(
            filename=filename,
            success_count=imported_count,
            duplicate_count=duplicate_count,
            upload_date=datetime.datetime.now()
        )
        db.add(history)
        
        db.commit()
        return imported_count
