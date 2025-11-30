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
    
    # Clean columns
    mapping_df.columns = [str(c).strip() for c in mapping_df.columns]
    if 'Unnamed: 0' in mapping_df.columns:
        mapping_df.drop(columns=['Unnamed: 0'], inplace=True)
        
    print(f"Mapping Columns: {mapping_df.columns.tolist()}")
    
    # 2. Read Report Sheet
    report_sheet = [s for s in xls.sheet_names if '부산물' in s and '처리' in s][0]
    report_df = pd.read_excel(xls, sheet_name=report_sheet, header=None)
    
    # 3. Find Header Row
    header_row_idx = None
    for idx, row in report_df.iterrows():
        row_str = row.astype(str).values
        if '구분' in row_str:
            header_row_idx = idx
            break
            
    if header_row_idx is None:
        raise ValueError("Could not find header row with '구분'")
        
    print(f"Header found at row {header_row_idx}")
    
    # 4. Identify Category Columns
    header_row = report_df.iloc[header_row_idx]
    category_cols = []
    for col_idx, val in enumerate(header_row):
        if str(val).strip() == '구분':
            category_cols.append(col_idx)
            
    print(f"Category columns found at indices: {category_cols}")
    
    if len(category_cols) < 2:
        print("Warning: Found fewer than 2 category columns. Assuming first is By-product.")
        
    # 5. Extract Items
    # Assuming first '구분' is By-product, second is Waste
    # Items are in the same column as '구분' header? No, usually '구분' is the header for the column.
    # Let's check the data below.
    
    by_products = []
    waste = []
    
    if len(category_cols) >= 1:
        col = category_cols[0]
        # Read from header_row + 1 until end or empty
        items = report_df.iloc[header_row_idx+1:, col].dropna().unique()
        # Filter out non-item strings if any (like '소계', '합계' etc)
        by_products = [str(i).strip() for i in items if str(i).strip() not in ['nan', '구분', '소계', '합계']]
        
    if len(category_cols) >= 2:
        col = category_cols[1]
        items = report_df.iloc[header_row_idx+1:, col].dropna().unique()
        waste = [str(i).strip() for i in items if str(i).strip() not in ['nan', '구분', '소계', '합계']]
        
    print(f"By-products: {by_products}")
    print(f"Waste: {waste}")
    
    item_cat_map = {}
    for item in by_products:
        item_cat_map[item] = '부산물'
    for item in waste:
        item_cat_map[item] = '폐기물'
        
    # 6. Update Mapping DataFrame
    # Ensure '연간처리 품명' exists
    target_col = '연간처리 품명'
    if target_col not in mapping_df.columns:
        # Try to find it
        for c in mapping_df.columns:
            if '연간처리' in c and '품명' in c:
                target_col = c
                break
    
    print(f"Using '{target_col}' for mapping.")
    
    def get_category(row):
        std_item = str(row[target_col]).strip()
        # Try exact match
        cat = item_cat_map.get(std_item)
        if cat: return cat
        
        # Try partial match?
        for k, v in item_cat_map.items():
            if k in std_item or std_item in k:
                return v
        return 'Unknown'

    mapping_df['구분'] = mapping_df.apply(get_category, axis=1)
    
    # 7. Save and Import
    mapping_df.to_excel(output_path, index=False)
    
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
    import traceback
    traceback.print_exc()
