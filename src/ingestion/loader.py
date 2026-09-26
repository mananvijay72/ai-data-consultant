"""
loader.py
---------
Reads a client's raw uploaded file (CSV or XLSX) into a pandas DataFrame.
Deliberately minimal — validation and cleaning happen in profiler.py /
standardizer.py, not here.
"""
import pandas as pd


def load_file(path: str) -> pd.DataFrame:
    if path.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(path)
    elif path.lower().endswith(".csv"):
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported file type: {path}. Use .csv or .xlsx")

    if df.empty:
        raise ValueError("Uploaded file has no rows.")
    return df
