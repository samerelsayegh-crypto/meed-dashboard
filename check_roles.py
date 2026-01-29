import pandas as pd
from data_loader import load_all_data

file_path = "ProjectListingExport-29-01-26-16-32-58.xlsx"
try:
    dfs = load_all_data(file_path)
    if 'Roles' in dfs:
        roles = dfs['Roles']['Role'].unique()
        print("Unique Roles found:", roles)
    else:
        print("Roles sheet not found.")
except Exception as e:
    print(e)
