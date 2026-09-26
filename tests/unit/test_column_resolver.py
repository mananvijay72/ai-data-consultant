from src.ingestion.standardizer import resolve_columns


def test_resolves_common_aliases():
    cols = ["Date", "Item", "Quantity", "Total", "Cost", "Table"]
    resolved = resolve_columns(cols)
    assert resolved["order_date"] == "Date"
    assert resolved["item_name"] == "Item"
    assert resolved["sale_amount"] == "Total"
    assert resolved["cost_amount"] == "Cost"
    assert resolved["table_id"] == "Table"


def test_unmatched_columns_are_absent():
    cols = ["SomeWeirdColumn"]
    resolved = resolve_columns(cols)
    assert "sale_amount" not in resolved


def test_case_and_whitespace_insensitive():
    cols = [" total ", "ORDER_DATE"]
    resolved = resolve_columns(cols)
    assert resolved["sale_amount"] == " total "
    assert resolved["order_date"] == "ORDER_DATE"
