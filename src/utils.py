import pandas as pd
import re

def find_header_row(df, keywords):
    """
    Finds the index of the row containing the keywords.
    Returns the index (integer) or None if not found.
    """
    # Check first 20 rows
    for i in range(min(20, len(df))):
        # Convert row to list of strings, removing all whitespace for comparison
        row_values = [str(val).replace(' ', '').replace('\n', '') for val in df.iloc[i].values]
        
        # Check if enough keywords are present in this row
        match_count = 0
        for k in keywords:
            k_clean = k.replace(' ', '')
            # Check if keyword is contained in any cell value
            if any(k_clean in val for val in row_values):
                match_count += 1
        
        if match_count >= 2: # At least 2 keywords match
            return i
    return None

def clean_column_names(df):
    """Cleans column names by removing whitespace and special chars."""
    df.columns = df.columns.astype(str).str.strip().str.replace(r'\s+', '', regex=True)
    return df

def parse_disposal_file(uploaded_file):
    """
    Parses 'Disposal' Excel file.
    Supports multiple formats:
    1. Standard: 품목, 단위, 단가, 구분, 차량, 담당, 특이사항
    2. Report: 계근량, 매각금액, 구분, 차량
    """
    all_data = []
    xls = pd.ExcelFile(uploaded_file)
    
    for sheet_name in xls.sheet_names:
        # Skip graph or summary sheets if possible
        if '그래프' in sheet_name or '세부현황' in sheet_name:
            # Note: '연간처리 세부현황' might contain data, but let's focus on main sheets first
            # If user wants '연간처리 세부현황', we can enable it.
            # Based on debug, '연간처리 세부현황' had data at row 9.
            pass
            
        try:
            # Read raw data to find header
            df_raw = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)
            
            # Try Format 1
            header_idx = find_header_row(df_raw, ['품목', '단가'])
            
            # Try Format 2 if Format 1 not found
            if header_idx is None:
                header_idx = find_header_row(df_raw, ['계근량', '매각금액'])
            
            if header_idx is not None:
                # Reload with correct header
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=header_idx)
                df = clean_column_names(df)
                
                # Rename columns to match DB schema
                rename_map = {
                    '날짜': 'transaction_date',
                    '일자': 'transaction_date',
                    '업체': 'vendor',
                    '품목': 'item',
                    '단위': 'unit',
                    '단가': 'unit_price',
                    '구분': 'category',
                    '차량': 'vehicle',
                    '담당': 'manager',
                    '특이사항': 'note',
                    '비고': 'note',
                    '계근량': 'quantity',
                    '수량': 'quantity',
                    '매각금액': 'amount',
                    '금액': 'amount'
                }
                df = df.rename(columns=rename_map)
                
                # Filter valid rows
                # If 'item' exists, use it. If not, maybe 'quantity' or 'amount'?
                if 'item' in df.columns:
                    df = df[df['item'].notna()]
                elif 'quantity' in df.columns:
                    df = df[df['quantity'].notna()]
                
                # Add missing columns with None
                for col in ['transaction_date', 'vendor', 'item', 'unit', 'unit_price', 'quantity', 'amount', 'category', 'vehicle', 'manager', 'note']:
                    if col not in df.columns:
                        df[col] = None
                        
                all_data.append(df)
        except Exception as e:
            print(f"Error parsing sheet {sheet_name}: {e}")
            
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None

def parse_gate_pass_file(uploaded_file):
    """
    Parses 'Gate Pass' Excel file.
    Expected columns: 날짜, 내용, 수량, 비고
    Sheets represent Vendors.
    """
    all_data = []
    xls = pd.ExcelFile(uploaded_file)
    
    for sheet_name in xls.sheet_names:
        try:
            # Read raw data
            df_raw = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=None)
            header_idx = find_header_row(df_raw, ['날짜', '내용', '수량'])
            
            if header_idx is not None:
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=header_idx)
                df = clean_column_names(df)
                
                # Rename map
                rename_map = {
                    '날짜': 'transaction_date',
                    '내용': 'content',
                    '품목': 'content',
                    '수량': 'quantity',
                    '비고': 'note',
                    '특이사항': 'note'
                }
                df = df.rename(columns=rename_map)
                
                # Vendor is the sheet name
                df['vendor'] = sheet_name
                
                # Filter valid rows
                if 'transaction_date' in df.columns:
                    df = df[df['transaction_date'].notna()]
                
                # Ensure columns exist
                for col in ['transaction_date', 'vendor', 'content', 'quantity', 'note']:
                    if col not in df.columns:
                        df[col] = None
                        
                all_data.append(df)
        except Exception as e:
            print(f"Error parsing sheet {sheet_name}: {e}")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return None
