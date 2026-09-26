"""
standardizer.py
---------------
Maps a client's messy, arbitrary column names to our canonical schema
names via an alias table. This is the single most important piece of
"realistic" engineering in the whole project: it's what lets the KPI
Engine work on a CSV that calls the revenue column "Total" instead of
"sale_amount" without any LLM call.

Two-stage resolution:
  1. Exact/alias match (this file) — fast, deterministic, zero cost.
  2. (Optional, not required for MVP) fuzzy/embedding fallback for columns
     that don't match any known alias — left as a documented extension
     point, see `resolve_columns_fuzzy_fallback` stub at the bottom.
"""
from typing import Dict, List

# Canonical name -> list of known aliases (lowercased, stripped comparison)
COLUMN_ALIASES: Dict[str, List[str]] = {
    "sale_amount": ["amount", "total", "revenue", "price_total", "net_sales",
                    "order_total", "sales", "total_price"],
    "order_date": ["date", "order_dt", "transaction_date", "created_at",
                   "order_date", "purchase_date"],
    "item_name": ["product", "item", "menu_item", "sku_name", "product_name"],
    "quantity": ["qty", "units", "count", "quantity"],
    "cost_amount": ["cost", "cogs", "unit_cost_total", "cost_of_goods"],
    "table_id": ["table", "table_number", "table_no"],
    "order_time": ["time", "order_time", "checkout_time"],
    "customer_id": ["customer", "cust_id", "client_id", "user_id"],
    "review_text": ["review", "feedback", "comment", "comments", "notes"],
    "category": ["category", "product_category", "department"],
    "discount_amount": ["discount", "discount_total", "promo_amount"],
    "return_flag": ["returned", "is_return", "return_status"],
}


def _normalize(name: str) -> str:
    """
    Lowercases and strips whitespace/underscores so 'OrderTotal',
    'order_total', and 'Order Total' all normalize to the same key.
    This one function is what makes alias matching robust to the many
    harmless ways client column names get formatted (CamelCase, snake_case,
    Title Case with spaces) without needing a fuzzy/embedding fallback.
    """
    return name.strip().lower().replace("_", "").replace(" ", "")


def resolve_columns(df_columns: List[str]) -> Dict[str, str]:
    """
    Returns {canonical_name: actual_client_column_name} for every canonical
    field that could be matched. Fields with no match are simply absent
    from the returned dict (the KPI engine treats that as "not available").
    """
    normalized = {_normalize(col): col for col in df_columns}
    resolved = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        candidates = [_normalize(a) for a in [canonical] + aliases]
        for candidate in candidates:
            if candidate in normalized:
                resolved[canonical] = normalized[candidate]
                break
    return resolved


def resolve_columns_fuzzy_fallback(unmatched_columns: List[str], canonical_names: List[str]) -> Dict[str, str]:
    """
    Extension point (not required for MVP): for columns that didn't match
    any alias exactly, embed the column name and the canonical field names
    with the same Gemini embedder used for RAG, and match by cosine
    similarity above a threshold. Left unimplemented intentionally —
    exact/alias matching is a legitimate, defensible v1; this is where a
    *small*, well-scoped LLM/embedding assist would go if extended.
    """
    raise NotImplementedError(
        "Fuzzy fallback not implemented in MVP — see docstring for the "
        "intended design if this is extended."
    )
