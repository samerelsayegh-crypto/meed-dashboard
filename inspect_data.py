import pandas as pd
import os

file_path = "ProjectListingExport-29-01-26-16-32-58.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    print(f"File found: {file_path}")
    print(f"Sheet names: {xl.sheet_names}")
    
    for sheet in xl.sheet_names:
        print(f"\n--- Sheet: {sheet} ---")
        df = xl.parse(sheet, nrows=5)
        print("Columns:")
        for col in df.columns:
            print(f"  - {col}")
        print("First 2 rows:")
        print(df.head(2))
        
except Exception as e:
    print(f"Error reading file: {e}")
