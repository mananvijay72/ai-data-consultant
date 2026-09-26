"""
ecommerce.py
------------
KPI registry for the "ecommerce" domain.
"""
from src.kpi_engine.base import monthly_trend, top_n, bottom_n

REGISTRY = [
    {
        "name": "gross_merchandise_value",
        "description": "Sum of all order totals (GMV).",
        "required_columns": ["sale_amount"],
        "func": lambda df: round(float(df["sale_amount"].sum()), 2),
    },
    {
        "name": "revenue_trend_monthly",
        "description": "GMV by month.",
        "required_columns": ["sale_amount", "order_date"],
        "func": lambda df: monthly_trend(df, "order_date", "sale_amount"),
    },
    {
        "name": "average_order_value",
        "description": "Average order value.",
        "required_columns": ["sale_amount"],
        "func": lambda df: round(float(df["sale_amount"].mean()), 2),
    },
    {
        "name": "top_selling_products",
        "description": "Top 5 products by revenue.",
        "required_columns": ["item_name", "sale_amount"],
        "func": lambda df: top_n(df, "item_name", "sale_amount"),
    },
    {
        "name": "bottom_selling_products",
        "description": "Bottom 5 products by revenue.",
        "required_columns": ["item_name", "sale_amount"],
        "func": lambda df: bottom_n(df, "item_name", "sale_amount"),
    },
    {
        "name": "repeat_customer_rate",
        "description": "Percentage of customers with more than 1 order.",
        "required_columns": ["customer_id"],
        "func": lambda df: round(
            float((df.groupby("customer_id").size() > 1).mean() * 100), 2
        ),
    },
    {
        "name": "return_rate_pct",
        "description": "Percentage of orders flagged as returned.",
        "required_columns": ["return_flag"],
        "func": lambda df: round(float(df["return_flag"].astype(bool).mean() * 100), 2),
    },
    {
        "name": "discount_share_of_revenue",
        "description": "Share of revenue that came from discounted orders.",
        "required_columns": ["discount_amount", "sale_amount"],
        "func": lambda df: round(
            float(df.loc[df["discount_amount"] > 0, "sale_amount"].sum() / df["sale_amount"].sum() * 100), 2
        ),
    },
]
