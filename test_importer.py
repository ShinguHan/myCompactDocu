from src.database import SessionLocal, engine, Base
from src.importer import parse_excel_and_import
from src.models import Transaction, Company, Item
import os

# Re-create tables
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

file_path = r'c:\Scripts\Dev\12.compactDocu\ref\25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx'

print(f"Testing importer with file: {file_path}")

try:
    count = parse_excel_and_import(file_path, db)
    print(f"Successfully imported {count} transactions.")
    
    # Verify data
    transactions = db.query(Transaction).all()
    print(f"Total transactions in DB: {len(transactions)}")
    
    if len(transactions) > 0:
        print("\nSample Transactions:")
        for t in transactions[:5]:
            print(f"Date: {t.date}, Company: {t.company.name}, Item: {t.item.name}, Qty: {t.quantity}, Amount: {t.total_amount}")
            
except Exception as e:
    print(f"Error during import: {e}")
finally:
    db.close()
