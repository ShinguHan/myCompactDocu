import pandas as pd
import os
from database import SessionLocal
from importers.mapping_importer import MappingImporter

file_path = os.path.join("ref", "25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx")
output_path = "corrected_mapping.xlsx"

try:
    xls = pd.ExcelFile(file_path)
    print(f"All Sheet Names: {xls.sheet_names}")
    
    # 1. Read Mapping Sheet
    # Try exact match first
    mapping_sheet_name = '폐기물 업체 Mapping'
    if mapping_sheet_name not in xls.sheet_names:
        # Fallback
        mapping_sheet_name = [s for s in xls.sheet_names if 'Mapping' in s][0]
    
    print(f"Reading Mapping Sheet: {mapping_sheet_name}")
    mapping_df_raw = pd.read_excel(xls, sheet_name=mapping_sheet_name, header=None)
    
    # Find header row for Mapping
    map_header_idx = None
    for idx, row in mapping_df_raw.iterrows():
        if '품명' in row.astype(str).values:
            map_header_idx = idx
            break
            
    if map_header_idx is None:
        raise ValueError("Could not find '품명' in mapping sheet.")
        
    # Reload with correct header
    mapping_df = pd.read_excel(xls, sheet_name=mapping_sheet_name, header=map_header_idx)
    mapping_df.columns = [str(c).strip() for c in mapping_df.columns]
    
    # Drop Unnamed
    mapping_df = mapping_df.loc[:, ~mapping_df.columns.str.contains('^Unnamed')]
    
    print(f"Mapping Columns: {mapping_df.columns.tolist()}")
    
    # 2. Read Report Sheet
    # Try to find sheet with '부산물' and '처리'
    report_sheet_name = None
    for s in xls.sheet_names:
        if '부산물' in s and '처리' in s:
            report_sheet_name = s
            break
            
    if not report_sheet_name:
        # Fallback to first sheet if not mapping
        for s in xls.sheet_names:
            if s != mapping_sheet_name:
                report_sheet_name = s
                break
                
    print(f"Reading Report Sheet: {report_sheet_name}")
    report_df = pd.read_excel(xls, sheet_name=report_sheet_name, header=None)
    
    # 3. Find Header Row for Report
    rep_header_idx = None
    for idx, row in report_df.iterrows():
        if '구분' in row.astype(str).values:
            rep_header_idx = idx
            break
            
    if rep_header_idx is None:
        raise ValueError("Could not find '구분' in report sheet.")
        
    print(f"Report Header found at row {rep_header_idx}")
    
    # 4. Identify Category Columns
    header_row = report_df.iloc[rep_header_idx]
    category_cols = []
    for col_idx, val in enumerate(header_row):
        if str(val).strip() == '구분':
            category_cols.append(col_idx)
            
    print(f"Category columns found at indices: {category_cols}")
    
    # 5. Extract Items
    by_products = []
    waste = []
    
    if len(category_cols) >= 1:
        col = category_cols[0]
        items = report_df.iloc[rep_header_idx+1:, col].dropna().unique()
        by_products = [str(i).strip() for i in items if str(i).strip() not in ['nan', '구분', '소계', '합계']]
        
    if len(category_cols) >= 2:
        col = category_cols[1]
        items = report_df.iloc[rep_header_idx+1:, col].dropna().unique()
        waste = [str(i).strip() for i in items if str(i).strip() not in ['nan', '구분', '소계', '합계']]
        
    print(f"By-products: {by_products}")
    print(f"Waste: {waste}")
    
    item_cat_map = {}
    for item in by_products:
        item_cat_map[item] = '부산물'
    for item in waste:
        item_cat_map[item] = '폐기물'
        
    # 6. Update Mapping DataFrame
    target_col = '연간처리 품명'
    if target_col not in mapping_df.columns:
        raise ValueError(f"Column '{target_col}' not found in mapping sheet.")
    
    def get_category(row):
        std_item = str(row[target_col]).strip()
        cat = item_cat_map.get(std_item)
        if cat: return cat
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
