"""
profiler.py
-----------
Builds a lightweight "dataset profile" dict describing the uploaded data:
shape, dtypes, null rates, detected date range, and a small sample of rows.
This profile is published as `artifact://dataset/profile` and is what the
Domain Classifier agent reasons over (it never sees the full dataset).
"""
import pandas as pd
from typing import Any, Dict


def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    profile = {
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_percentage": {
            col: round(df[col].isnull().mean() * 100, 2) for col in df.columns
        },
        "sample_rows": df.head(5).to_dict(orient="records"),
    }

    # try to detect a date-like column and its range, useful context for
    # both the classifier and later seasonal narrative reasoning
    date_col = _detect_date_column(df)
    if date_col:
        parsed = pd.to_datetime(df[date_col], errors="coerce")
        profile["detected_date_column"] = date_col
        profile["date_range"] = {
            "start": str(parsed.min()),
            "end": str(parsed.max()),
        }

    # detect a likely free-text review/feedback column (long avg string length)
    text_col = _detect_text_column(df)
    if text_col:
        profile["detected_text_column"] = text_col

    return profile


def _detect_date_column(df: pd.DataFrame) -> str | None:
    candidates = [c for c in df.columns if any(
        kw in c.lower() for kw in ["date", "time", "created_at", "dt"]
    )]
    for c in candidates:
        parsed = pd.to_datetime(df[c], errors="coerce")
        if parsed.notnull().mean() > 0.7:  # most values parse as dates
            return c
    return None


def _detect_text_column(df: pd.DataFrame, min_avg_len: int = 25) -> str | None:
    best_col, best_len = None, 0
    for c in df.columns:
        if df[c].dtype == object:
            avg_len = df[c].dropna().astype(str).str.len().mean()
            if avg_len and avg_len > min_avg_len and avg_len > best_len:
                best_col, best_len = c, avg_len
    return best_col
