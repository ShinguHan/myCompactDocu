import pandas as pd
import os

file_path = os.path.join("ref", "25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx")

try:
    xls = pd.ExcelFile(file_path)
    print(f"Sheet names found: {xls.sheet_names}")
    
    # Try to identify the report sheet (likely the first one or one with '부산물')
    report_sheet = None
    for s in xls.sheet_names:
        if '부산물' in s and '처리' in s:
            report_sheet = s
            break
    
    if report_sheet:
        print(f"Reading sheet: {report_sheet}")
        df = pd.read_excel(xls, sheet_name=report_sheet, header=None, nrows=20)
        print(df.to_string())
    else:
        print("Could not identify report sheet.")

except Exception as e:
    print(f"Error reading file: {e}")
