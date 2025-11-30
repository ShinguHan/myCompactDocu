import pandas as pd
from database import SessionLocal
from importers.mapping_importer import MappingImporter
from models import ReportMapping
import os

# Create dummy Excel
data = {
    '품명': ['Item A', 'Item B'],
    '업체명': ['Company A', 'Company B'],
    '연간처리 품명': ['Std Item A', 'Std Item B'],
    '연간처리 업체': ['Std Company A', 'Std Company B'],
    '구분': ['부산물', '폐기물']
}
df = pd.DataFrame(data)
filename = "test_mapping.xlsx"
df.to_excel(filename, index=False)

# Run Importer
print("Running importer...")
db = SessionLocal()
importer = MappingImporter()
try:
    # We need to open the file as binary for the importer (it expects file-like or path? pandas read_excel handles both)
    # The importer uses pd.ExcelFile(file_input)
    with open(filename, 'rb') as f:
        parsed_data = importer.parse(f)
        print(f"Parsed {len(parsed_data)} rows.")
        print(parsed_data[0])
        
        count = importer.save(parsed_data, db, filename)
        print(f"Saved {count} mappings.")

    # Verify DB
    m = db.query(ReportMapping).first()
    print(f"DB Record: Raw={m.raw_item}, Cat={m.category}")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
    if os.path.exists(filename):
        os.remove(filename)
