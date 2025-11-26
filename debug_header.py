import pandas as pd
import os

REF_DIR = r'c:\Scripts\Dev\12.compactDocu\ref'
DISPOSAL_FILE = os.path.join(REF_DIR, '25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx')

def inspect_header(file, sheet_name):
    print(f"\n--- Inspecting {sheet_name} ---")
    try:
        df = pd.read_excel(file, sheet_name=sheet_name, header=None, nrows=20)
        for i in range(len(df)):
            # Print row index and values, replacing NaNs with empty string for readability
            row_vals = [str(x) if pd.notna(x) else '' for x in df.iloc[i].tolist()]
            print(f"Row {i}: {row_vals}")
    except Exception as e:
        print(f"Error: {e}")

inspect_header(DISPOSAL_FILE, '연간처리 세부현황')
