from database import SessionLocal
from models import ReportMapping
import pandas as pd

db = SessionLocal()
mappings = pd.read_sql(db.query(ReportMapping).statement, db.bind)
print(mappings.head(10).to_string())
print(f"\nTotal mappings: {len(mappings)}")
print(f"Mappings with Category: {mappings['category'].count()}")
db.close()
