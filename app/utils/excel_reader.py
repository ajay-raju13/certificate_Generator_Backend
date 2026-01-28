import pandas as pd

def read_excel_rows(path):
    df = pd.read_excel(path)
    df = df.fillna("")
    return df.to_dict(orient="records")

def get_excel_headers(path):
    """Get column headers from Excel file"""
    df = pd.read_excel(path)
    return df.columns.tolist()
