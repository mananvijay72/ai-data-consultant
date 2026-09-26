import pandas as pd
from src.kpi_engine.base import run_kpi_engine
from src.kpi_engine.restaurant import REGISTRY as RESTAURANT_REGISTRY
from src.kpi_engine.ecommerce import REGISTRY as ECOMMERCE_REGISTRY


def test_restaurant_kpis_compute_on_sample_data():
    df = pd.read_csv("data/samples/restaurant_sales_sample.csv")
    result = run_kpi_engine(df, RESTAURANT_REGISTRY)
    assert "total_revenue" in result["computed"]
    assert result["computed"]["total_revenue"] > 0
    assert "food_cost_percentage" in result["computed"]
    assert 0 < result["computed"]["food_cost_percentage"] < 100
    assert result["skipped"] == []  # sample data has all required columns


def test_ecommerce_kpis_compute_on_sample_data():
    df = pd.read_csv("data/samples/ecommerce_orders_sample.csv")
    result = run_kpi_engine(df, ECOMMERCE_REGISTRY)
    assert "gross_merchandise_value" in result["computed"]
    assert "return_rate_pct" in result["computed"]
    assert 0 <= result["computed"]["return_rate_pct"] <= 100


def test_missing_columns_are_skipped_not_crashed():
    df = pd.DataFrame({"Total": [10, 20, 30]})
    result = run_kpi_engine(df, RESTAURANT_REGISTRY)
    assert "total_revenue" in result["computed"]
    skipped_names = [s["kpi"] for s in result["skipped"]]
    assert "food_cost_percentage" in skipped_names
    reason = next(s["reason"] for s in result["skipped"] if s["kpi"] == "food_cost_percentage")
    assert "cost_amount" in reason
