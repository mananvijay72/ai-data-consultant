"""
Integration test for the RAG layer. Requires GEMINI_API_KEY since it
calls the real embedding API — this is intentional: RAG retrieval quality
can only be verified against real embeddings, not mocked.

Run manually after building the corpus:
    python -m src.rag.cli build --domain restaurant
    python -m src.rag.cli build --domain ecommerce
    pytest tests/integration/test_rag_end_to_end.py
"""
import os
import pytest
from src.rag.retriever import query


@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="requires GEMINI_API_KEY")
def test_restaurant_retrieval_returns_relevant_doc():
    results = query("restaurant", "what is a healthy food cost percentage?", top_k=3)
    sources = [r.source for r in results]
    assert "food_cost_benchmarks.md" in sources


@pytest.mark.skipif(not os.environ.get("GEMINI_API_KEY"), reason="requires GEMINI_API_KEY")
def test_ecommerce_retrieval_returns_relevant_doc():
    results = query("ecommerce", "what is a good LTV to CAC ratio?", top_k=3)
    sources = [r.source for r in results]
    assert "aov_cac_benchmarks.md" in sources
