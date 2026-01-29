import pandas as pd
import streamlit as st

@st.cache_data
def load_all_data(file_path):
    """
    Loads all sheets from the Excel file and performs basic cleaning.
    Returns a dictionary of DataFrames.
    """
    try:
        xls = pd.ExcelFile(file_path)
        data_frames = {}
        
        # 1. Load Projects (Main Data)
        if 'Projects' in xls.sheet_names:
            df_projects = xls.parse('Projects')
            # Clean columns: strip whitespace and replace non-breaking spaces
            df_projects.columns = df_projects.columns.str.replace(r'\xa0', ' ', regex=True).str.strip()
            print(f"DEBUG: Projects Columns: {df_projects.columns.tolist()}")
            
            # Numeric conversion
            numeric_cols = ['Net Project Value ($m)', 'Contract Value ($m)', 
                           'Estimated Budget ($m)', 'Cash Spent ($m)']
            for col in numeric_cols:
                if col in df_projects.columns:
                    df_projects[col] = pd.to_numeric(df_projects[col], errors='coerce').fillna(0)
            
            # Year cleaning
            if 'AwardYear' in df_projects.columns:
                df_projects['AwardYear'] = pd.to_numeric(df_projects['AwardYear'], errors='coerce')
            if 'CompletionYear' in df_projects.columns:
                df_projects['CompletionYear'] = pd.to_numeric(df_projects['CompletionYear'], errors='coerce')

            data_frames['Projects'] = df_projects
        
        # 2. Load Roles
        if 'Projects with Roles' in xls.sheet_names:
            df_roles = xls.parse('Projects with Roles')
            df_roles.columns = df_roles.columns.str.strip()
            data_frames['Roles'] = df_roles

        # 3. Load Events
        if 'Projects with Events' in xls.sheet_names:
            df_events = xls.parse('Projects with Events')
            df_events.columns = df_events.columns.str.strip()
            # Date cleaning
            if 'EventDate' in df_events.columns:
                df_events['EventDate'] = pd.to_datetime(df_events['EventDate'], errors='coerce')
            data_frames['Events'] = df_events

        # 4. Load Products
        if 'Projects with Products' in xls.sheet_names:
            df_products = xls.parse('Projects with Products')
            df_products.columns = df_products.columns.str.strip()
            if 'Quantity' in df_products.columns:
                 df_products['Quantity'] = pd.to_numeric(df_products['Quantity'], errors='coerce').fillna(0)
            data_frames['Products'] = df_products

        # Post-processing: Clean columns for ALL loaded dataframes
        for key in data_frames:
            df = data_frames[key]
            # Strip whitespace and replace NBSP
            df.columns = df.columns.astype(str).str.replace(r'\xa0', ' ', regex=True).str.strip()
            # Standardize ID column
            rename_map = {'New ProjectId': 'New_ProjectId', 'Old ProjectId': 'Old_ProjectId'}
            df.rename(columns=rename_map, inplace=True)
            data_frames[key] = df
            print(f"DEBUG: {key} Columns: {df.columns.tolist()}")

        return data_frames

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None
