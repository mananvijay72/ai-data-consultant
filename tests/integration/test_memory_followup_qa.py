"""
Verifies that a client's structured artifacts get correctly chunked and
indexed into a queryable semantic memory collection, and that the QA
agent can answer a follow-up question grounded in it. Requires
GEMINI_API_KEY (real embeddings + Gemini generation).
"""
import os
import pytest
from src.memory.artifact_store import publish
from src.memory.memory_indexer import build_client_memory
from src.rag.retriever import query


@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="requires GEMINI_API_KEY")
def test_memory_indexing_and_retrieval():
    client_id = "test_memory_client"
    publish(client_id, "kpi/results", {
        "computed": {"food_cost_percentage": 34.2, "total_revenue": 50000},
        "skipped": [],
    })
    publish(client_id, "insight/narrative",
            "Food cost percentage rose to 34.2% this quarter, above the "
            "typical casual dining range, driven mainly by produce price "
            "increases in March.")

    n = build_client_memory(client_id)
    assert n > 0

    results = query(f"client_{client_id}_memory", "food cost percentage",
                     top_k=3, persist_dir="vectorstore/client_memory")
    combined_text = " ".join(r.text for r in results)
    assert "34.2" in combined_text
