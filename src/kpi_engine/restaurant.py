"""
restaurant.py
-------------
KPI registry for the "restaurant" domain. Each entry declares the
canonical columns it needs (see standardizer.COLUMN_ALIASES for how
client column names map to these).
"""
import pandas as pd
from src.kpi_engine.base import monthly_trend, top_n, bottom_n

REGISTRY = [
    {
        "name": "total_revenue",
        "description": "Sum of all sale amounts in the period.",
        "required_columns": ["sale_amount"],
        "func": lambda df: round(float(df["sale_amount"].sum()), 2),
    },
    {
        "name": "revenue_trend_monthly",
        "description": "Total revenue by month.",
        "required_columns": ["sale_amount", "order_date"],
        "func": lambda df: monthly_trend(df, "order_date", "sale_amount"),
    },
    {
        "name": "average_order_value",
        "description": "Average sale amount per order.",
        "required_columns": ["sale_amount"],
        "func": lambda df: round(float(df["sale_amount"].mean()), 2),
    },
    {
        "name": "top_selling_items",
        "description": "Top 5 items by revenue.",
        "required_columns": ["item_name", "sale_amount"],
        "func": lambda df: top_n(df, "item_name", "sale_amount"),
    },
    {
        "name": "bottom_selling_items",
        "description": "Bottom 5 items by revenue.",
        "required_columns": ["item_name", "sale_amount"],
        "func": lambda df: bottom_n(df, "item_name", "sale_amount"),
    },
    {
        "name": "food_cost_percentage",
        "description": "(cost_amount / sale_amount) * 100.",
        "required_columns": ["cost_amount", "sale_amount"],
        "func": lambda df: round(float(df["cost_amount"].sum() / df["sale_amount"].sum() * 100), 2),
    },
    {
        "name": "avg_table_turnover",
        "description": "Average number of distinct orders per table.",
        "required_columns": ["table_id"],
        "func": lambda df: round(float(df.groupby("table_id").size().mean()), 2),
    },
]
