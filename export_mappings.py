import pandas as pd
from database import SessionLocal
from models import ReportMapping

db = SessionLocal()
mappings = pd.read_sql(db.query(ReportMapping).statement, db.bind)
db.close()

output_file = "debug_report_mappings_dump.csv"
mappings.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f"Exported {len(mappings)} mappings to {output_file}")
print("First 5 rows:")
print(mappings.head().to_string())
