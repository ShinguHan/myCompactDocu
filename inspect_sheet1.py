import pandas as pd
import os

file_path = os.path.join("ref", "25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx")

try:
    df = pd.read_excel(file_path, sheet_name='Sheet1', nrows=10)
    print(df.to_string())
except Exception as e:
    print(f"Error reading file: {e}")
