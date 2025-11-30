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
    # Debug columns
    print(f"Original Mapping Columns: {mapping_df.columns.tolist()}")
    mapping_df.columns = [str(c).strip() for c in mapping_df.columns]
    print(f"Stripped Mapping Columns: {mapping_df.columns.tolist()}")
    
    # 2. Read Report Sheet
    report_sheet = [s for s in xls.sheet_names if '부산물' in s and '처리' in s][0]
    report_df = pd.read_excel(xls, sheet_name=report_sheet, header=None)
    
    # Debug Report Sheet
    print("Report Sheet Head (Rows 0-5, Cols 0-15):")
    print(report_df.iloc[:5, :15].to_string())
    
    # 3. Extract Categories
    # Adjust indices based on debug output
    # Assuming Left (Col 2, index 2) is By-product, Right (Col 8, index 8) is Waste
    
    by_products = report_df.iloc[2:, 2].dropna().unique()
    waste = report_df.iloc[2:, 8].dropna().unique()
    
    print(f"By-products (Col 2): {by_products}")
    print(f"Waste (Col 8): {waste}")
    
    item_cat_map = {}
    for item in by_products:
        item_cat_map[str(item).strip()] = '부산물'
    for item in waste:
        item_cat_map[str(item).strip()] = '폐기물'
        
    # 4. Update Mapping DataFrame
    if '연간처리 품명' not in mapping_df.columns:
        # Try to find close match
        for c in mapping_df.columns:
            if '연간처리' in c and '품명' in c:
                print(f"Found similar column: {c}")
                mapping_df.rename(columns={c: '연간처리 품명'}, inplace=True)
    
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
    
    with open(output_path, 'rb') as f:
        data = importer.parse(f)
        count = importer.save(data, db, output_path)
        
    db.close()
    print(f"Successfully imported {count} mappings with categories.")

except Exception as e:
    print(f"Error: {e}")
