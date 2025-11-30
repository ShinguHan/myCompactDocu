import pandas as pd
import os

file_path = os.path.join("ref", "25년_08월_부산물 매각 및 폐기물 처리현황_돔황쳐_2.xlsx")

try:
    xls = pd.ExcelFile(file_path)
    # Find sheet again
    report_sheet = [s for s in xls.sheet_names if '부산물' in s][0]
    
    df = pd.read_excel(xls, sheet_name=report_sheet, header=None, nrows=3)
    print(df.iloc[:, :15].to_string())
except Exception as e:
    print(f"Error reading file: {e}")
