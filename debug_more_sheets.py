import pandas as pd
import os

REF_DIR = r'c:\Scripts\Dev\12.compactDocu\ref'
DISPOSAL_FILE = os.path.join(REF_DIR, '25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx')

def inspect_sheet(file, sheet_name):
    print(f"\n--- Inspecting {sheet_name} in {os.path.basename(file)} ---")
    try:
        df = pd.read_excel(file, sheet_name=sheet_name, header=None, nrows=20)
        for i in range(len(df)):
            print(f"Row {i}: {df.iloc[i].tolist()}")
    except Exception as e:
        print(f"Error: {e}")

inspect_sheet(DISPOSAL_FILE, '부산물 페기물 처리현황')
inspect_sheet(DISPOSAL_FILE, '연간처리 세부현황')
