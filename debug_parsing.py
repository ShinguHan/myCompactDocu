import pandas as pd
import os

REF_DIR = r'c:\Scripts\Dev\12.compactDocu\ref'
DISPOSAL_FILE = os.path.join(REF_DIR, '25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx')
GATE_PASS_FILE = os.path.join(REF_DIR, '반출증_2025011 새버젼.xlsx')

def inspect(file, name):
    print(f"\n--- Inspecting {name} ---")
    try:
        xls = pd.ExcelFile(file)
        print(f"Sheets: {xls.sheet_names}")
        for sheet in xls.sheet_names[:2]: # Check first 2 sheets
            print(f"\n[Sheet: {sheet}]")
            df = pd.read_excel(file, sheet_name=sheet, header=None, nrows=20)
            print(df.to_string())
    except Exception as e:
        print(f"Error: {e}")

inspect(DISPOSAL_FILE, "Disposal File")
inspect(GATE_PASS_FILE, "Gate Pass File")
