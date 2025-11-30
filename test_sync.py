from database import SessionLocal
from services.report_service import ReportService

try:
    db = SessionLocal()
    service = ReportService(db)
    print("Calling sync_mappings...")
    count = service.sync_mappings()
    print(f"Success! Synced {count} new mappings.")
    db.close()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
