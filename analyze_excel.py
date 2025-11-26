import pandas as pd
import os

REF_DIR = r'c:\Scripts\Dev\12.compactDocu\ref'
FILES = [
    '25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx',
    '반출증_2025011 새버젼.xlsx'
]

def analyze_file(filename):
    path = os.path.join(REF_DIR, filename)
    print(f"--- Analyzing: {filename} ---")
    try:
        xls = pd.ExcelFile(path)
        print(f"Sheets: {xls.sheet_names}")
        
        for sheet in xls.sheet_names:
            print(f"\n[Sheet: {sheet}]")
            try:
                # Read first few rows to infer header and structure
                df = pd.read_excel(path, sheet_name=sheet, nrows=5)
                print("Columns:", df.columns.tolist())
                print("Sample Data:")
                print(df.head(2).to_string())
            except Exception as e:
                print(f"  Error reading sheet: {e}")
    except Exception as e:
        print(f"Error opening file: {e}")
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    for f in FILES:
        analyze_file(f)
