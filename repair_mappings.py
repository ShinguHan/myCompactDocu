import pandas as pd
import os
from database import SessionLocal
from importers.mapping_importer import MappingImporter

file_path = os.path.join("ref", "25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx")
output_path = "corrected_mapping.xlsx"

try:
    xls = pd.ExcelFile(file_path)
    
    # 1. Read Mapping Sheet
    mapping_sheet = [s for s in xls.sheet_names if 'Mapping' in s][0]
    mapping_df = pd.read_excel(xls, sheet_name=mapping_sheet)
    mapping_df.columns = [str(c).strip() for c in mapping_df.columns]
    
    # 2. Read Report Sheet
    report_sheet = [s for s in xls.sheet_names if '부산물' in s and '처리' in s][0]
    report_df = pd.read_excel(xls, sheet_name=report_sheet, header=None)
    
    # 3. Extract Categories
    # Assuming Left (Col 2, index 2) is By-product, Right (Col 8, index 8) is Waste
    # Rows 2 onwards (index 2 onwards)
    
    by_products = report_df.iloc[2:, 2].dropna().unique()
    waste = report_df.iloc[2:, 8].dropna().unique()
    
    item_cat_map = {}
    for item in by_products:
        item_cat_map[str(item).strip()] = '부산물'
    for item in waste:
        item_cat_map[str(item).strip()] = '폐기물'
        
    print(f"Found {len(by_products)} By-products and {len(waste)} Waste items.")
    
    # 4. Update Mapping DataFrame
    # Map based on '연간처리 품명' (Standard Item)
    def get_category(row):
        std_item = str(row['연간처리 품명']).strip()
        return item_cat_map.get(std_item, 'Unknown')

    mapping_df['구분'] = mapping_df.apply(get_category, axis=1)
    
    # 5. Save to Excel
    mapping_df.to_excel(output_path, index=False)
    print(f"Saved corrected mapping to {output_path}")
    
    # 6. Import to DB
    print("Importing to database...")
    db = SessionLocal()
    importer = MappingImporter()
    
    # Re-read the file we just saved to ensure format matches what importer expects
    with open(output_path, 'rb') as f:
        data = importer.parse(f)
        count = importer.save(data, db, output_path)
        
    db.close()
    print(f"Successfully imported {count} mappings with categories.")

except Exception as e:
    print(f"Error: {e}")
