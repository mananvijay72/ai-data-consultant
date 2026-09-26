"""
base.py
-------
Runs a domain's KPI registry against a (renamed) dataframe. Each KPI
declares its required canonical columns; a KPI only runs if all its
required columns were resolved by standardizer.resolve_columns. KPIs that
can't run are reported as "skipped" with a reason, not silently dropped
and not hallucinated — this feeds directly into the Insight Analyst
agent's prompt so it never claims a number that wasn't actually computed.
"""
import pandas as pd
from typing import Any, Callable, Dict, List, TypedDict
from src.ingestion.standardizer import resolve_columns


class KPIDefinition(TypedDict):
    name: str
    description: str
    required_columns: List[str]
    func: Callable[[pd.DataFrame], Any]


def run_kpi_engine(df: pd.DataFrame, registry: List[KPIDefinition]) -> Dict[str, Any]:
    column_map = resolve_columns(list(df.columns))  # canonical -> actual
    inverse_rename = {actual: canonical for canonical, actual in column_map.items()}
    renamed_df = df.rename(columns=inverse_rename)

    computed: Dict[str, Any] = {}
    skipped: List[Dict[str, str]] = []

    for kpi in registry:
        missing = [c for c in kpi["required_columns"] if c not in column_map]
        if missing:
            skipped.append({
                "kpi": kpi["name"],
                "reason": f"missing required data: {', '.join(missing)}",
            })
            continue
        try:
            computed[kpi["name"]] = kpi["func"](renamed_df)
        except Exception as e:
            skipped.append({"kpi": kpi["name"], "reason": f"computation error: {e}"})

    return {
        "computed": computed,
        "skipped": skipped,
        "column_map": column_map,
    }


# ---- shared helper functions used by multiple domain registries ----

def monthly_trend(df: pd.DataFrame, date_col: str, value_col: str) -> Dict[str, float]:
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col])
    monthly = d.groupby(d[date_col].dt.to_period("M"))[value_col].sum()
    return {str(period): round(float(val), 2) for period, val in monthly.items()}


def top_n(df: pd.DataFrame, group_col: str, value_col: str, n: int = 5) -> Dict[str, float]:
    grouped = df.groupby(group_col)[value_col].sum().sort_values(ascending=False).head(n)
    return {str(k): round(float(v), 2) for k, v in grouped.items()}


def bottom_n(df: pd.DataFrame, group_col: str, value_col: str, n: int = 5) -> Dict[str, float]:
    grouped = df.groupby(group_col)[value_col].sum().sort_values(ascending=True).head(n)
    return {str(k): round(float(v), 2) for k, v in grouped.items()}
