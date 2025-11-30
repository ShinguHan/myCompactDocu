from database import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE report_mappings ADD COLUMN category VARCHAR"))
        print("Added category column.")
    except Exception as e:
        print(f"Column might already exist or error: {e}")
