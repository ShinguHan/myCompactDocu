import pandas as pd
import os

REF_DIR = r'c:\Scripts\Dev\12.compactDocu\ref'
DISPOSAL_FILE = os.path.join(REF_DIR, '25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx')
GATE_PASS_FILE = os.path.join(REF_DIR, '반출증_2025011 새버젼.xlsx')

def inspect_sheet(file, sheet_name):
    print(f"\n--- Inspecting {sheet_name} in {os.path.basename(file)} ---")
    try:
        df = pd.read_excel(file, sheet_name=sheet_name, header=None, nrows=15)
        print(df.to_string())
    except Exception as e:
        print(f"Error: {e}")

inspect_sheet(DISPOSAL_FILE, '부산물 페기물 처리현황')
inspect_sheet(GATE_PASS_FILE, 'Sheet1')
