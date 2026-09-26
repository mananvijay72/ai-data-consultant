"""
Integration test covering the deterministic half of the pipeline
(ingestion -> profiling -> KPI engine) without requiring a Gemini API key.
The agent/LLM-dependent stages (classification, narrative, business
section) are exercised only when GEMINI_API_KEY is set — see
test_pipeline_restaurant.py's skip condition.
"""
import os
import pandas as pd
import pytest
from src.ingestion.loader import load_file
from src.ingestion.profiler import profile_dataset
from src.kpi_engine.base import run_kpi_engine
from src.kpi_engine.restaurant import REGISTRY as RESTAURANT_REGISTRY


def test_full_deterministic_path_restaurant():
    df = load_file("data/samples/restaurant_sales_sample.csv")
    profile = profile_dataset(df)
    assert profile["row_count"] > 0
    assert "detected_date_column" in profile

    kpi_result = run_kpi_engine(df, RESTAURANT_REGISTRY)
    assert kpi_result["skipped"] == []
    assert kpi_result["computed"]["total_revenue"] > 0


@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="requires GEMINI_API_KEY")
def test_full_pipeline_with_llm_agents():
    from src.orchestrator import run_pipeline
    result = run_pipeline("data/samples/restaurant_sales_sample.csv", client_id="test_integration")
    assert result["domain"] == "restaurant"
    assert os.path.exists(result["html_path"])
    assert os.path.exists(result["pdf_path"])
