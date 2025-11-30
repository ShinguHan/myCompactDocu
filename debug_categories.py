from database import SessionLocal
from models import ReportMapping, Transaction, Company, Item
import pandas as pd

db = SessionLocal()

print("--- Checking ReportMapping Updates ---")
# Check if any categories are set to '부산물' or '폐기물'
known_cats = db.query(ReportMapping).filter(ReportMapping.category.in_(['부산물', '폐기물'])).count()
unknown_cats = db.query(ReportMapping).filter(ReportMapping.category == 'Unknown').count()
null_cats = db.query(ReportMapping).filter(ReportMapping.category == None).count()

print(f"Mappings with Known Category: {known_cats}")
print(f"Mappings with Unknown Category: {unknown_cats}")
print(f"Mappings with NULL Category: {null_cats}")

# Show a few examples
print("\nExample Mappings:")
mappings = pd.read_sql(db.query(ReportMapping).statement, db.bind)
print(mappings.head(10).to_string())

print("\n--- Checking Unmapped Transactions ---")
# Fetch all transactions
transactions = db.query(
    Transaction.date,
    Company.name.label("raw_company"),
    Item.name.label("raw_item")
).join(Company).join(Item).all()

print(f"Total Transactions: {len(transactions)}")

# Check which ones match mappings
unmapped_count = 0
for t in transactions:
    match = db.query(ReportMapping).filter(
        ReportMapping.raw_item == t.raw_item,
        ReportMapping.raw_company == t.raw_company
    ).first()
    
    if not match:
        print(f"Unmapped Transaction: Company='{t.raw_company}', Item='{t.raw_item}'")
        unmapped_count += 1
    elif match.category not in ['부산물', '폐기물']:
        # Mapped but category is still unknown/null
        pass # We already counted these in the mapping check

print(f"Total Unmapped Transactions: {unmapped_count}")

db.close()
