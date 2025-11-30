import pandas as pd
import os

file_path = os.path.join("ref", "25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx")

try:
    xls = pd.ExcelFile(file_path)
    print(f"Sheet names: {[repr(s) for s in xls.sheet_names]}")
except Exception as e:
    print(f"Error reading file: {e}")
