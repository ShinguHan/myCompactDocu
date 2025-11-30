import pandas as pd
import os

file_path = r'c:\Scripts\Dev\12.compactDocu\ref\25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx'
sheets_to_analyze = ['부산물 페기물 처리현황 (2)', '연간처리 세부현황', '폐기물 업체 Mapping']

print(f"Analyzing file: {file_path}")

try:
    # Read all sheets at once to avoid opening the file multiple times
    xls = pd.ExcelFile(file_path)
    
    with open('analysis_result.txt', 'w', encoding='utf-8') as f:
        for sheet_name in sheets_to_analyze:
            f.write(f"\n{'='*50}\n")
            f.write(f"Sheet: {sheet_name}\n")
            f.write(f"{'='*50}\n")
            
            if sheet_name in xls.sheet_names:
                # Read without header to see the raw layout
                df = pd.read_excel(xls, sheet_name=sheet_name, nrows=20, header=None)
                
                f.write("\nFirst 20 rows (Raw):\n")
                f.write(df.to_string())
                f.write("\n")
            else:
                f.write(f"Sheet '{sheet_name}' not found.\n")
    
    print("Analysis complete. Results written to analysis_result.txt")

except Exception as e:
    print(f"Error reading excel file: {e}")
