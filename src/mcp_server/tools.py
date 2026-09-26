"""
tools.py
--------
Implementations of the MCP "Tools" (active, agent-invoked actions). Kept
as plain importable functions so they can be:
  (a) registered on the MCP server (server.py), and
  (b) unit-tested directly without spinning up a server or an LLM.
"""
from typing import Any, Dict, List
from src.rag.retriever import query as rag_query, format_context
from src.memory.artifact_store import read as read_artifact


def retrieve_benchmark(metric_name: str, domain: str) -> str:
    """
    Tool: looks up an industry benchmark/definition for a KPI metric from
    the static domain RAG corpus built in Phase 1.
    """
    chunks = rag_query(domain, metric_name, top_k=3)
    return format_context(chunks)


def get_kpi_detail(client_id: str, kpi_name: str) -> Dict[str, Any]:
    """
    Tool: returns the full computed value (e.g. a monthly time series) for
    a KPI, when the Insight Analyst agent wants to explain a summary number
    in more depth than the top-level KPI dict provides.
    """
    kpi_results = read_artifact(client_id, "kpi/results")
    if kpi_name in kpi_results.get("computed", {}):
        return {"kpi": kpi_name, "value": kpi_results["computed"][kpi_name]}
    skipped = next((s for s in kpi_results.get("skipped", []) if s["kpi"] == kpi_name), None)
    if skipped:
        return {"kpi": kpi_name, "status": "skipped", "reason": skipped["reason"]}
    return {"kpi": kpi_name, "status": "not_found"}


def analyze_sentiment_batch(review_texts: List[str]) -> Dict[str, Any]:
    """
    Tool: lightweight, deterministic sentiment scoring + theme extraction
    over a batch of review/feedback texts. Deliberately simple (keyword-
    based) rather than another LLM call — keeps this tool fast, free, and
    testable; swap in a real classifier later without changing the
    interface the Business Analyst agent calls.
    """
    POSITIVE_WORDS = {"great", "love", "excellent", "friendly", "fast", "delicious",
                       "amazing", "good", "clean", "fresh"}
    NEGATIVE_WORDS = {"slow", "cold", "rude", "small", "late", "bad", "dirty",
                       "expensive", "damaged", "wrong"}
    THEME_KEYWORDS = {
        "speed_of_service": {"slow", "wait", "fast", "quick", "delay"},
        "portion_size": {"small", "portion", "size", "tiny", "large"},
        "quality": {"fresh", "delicious", "cold", "bad", "amazing", "quality"},
        "staff": {"friendly", "rude", "staff", "service"},
        "cleanliness": {"clean", "dirty"},
        "value": {"expensive", "price", "value", "cheap"},
        "shipping_packaging": {"damaged", "packaging", "shipping", "wrong", "late"},
    }

    scores, theme_counts = [], {t: 0 for t in THEME_KEYWORDS}
    for text in review_texts:
        words = set(text.lower().split())
        pos = len(words & POSITIVE_WORDS)
        neg = len(words & NEGATIVE_WORDS)
        scores.append(1 if pos > neg else (-1 if neg > pos else 0))
        for theme, keywords in THEME_KEYWORDS.items():
            if words & keywords:
                theme_counts[theme] += 1

    total = len(review_texts) or 1
    avg_sentiment = sum(scores) / total
    top_themes = sorted(
        ({k: v for k, v in theme_counts.items() if v > 0}).items(),
        key=lambda kv: kv[1], reverse=True
    )[:5]

    return {
        "average_sentiment": round(avg_sentiment, 3),
        "positive_pct": round(100 * sum(1 for s in scores if s > 0) / total, 1),
        "negative_pct": round(100 * sum(1 for s in scores if s < 0) / total, 1),
        "themes": [t for t, _ in top_themes],
        "theme_counts": dict(top_themes),
    }


def query_client_memory(client_id: str, question: str) -> str:
    """
    Tool: semantic retrieval over a client's own memory collection (built
    by memory_indexer.py after the report was generated). Used by
    qa_agent.py to answer follow-up questions grounded in the client's
    actual computed results.
    """
    collection_name = f"client_{client_id}_memory"
    chunks = rag_query(collection_name, question, top_k=4,
                        persist_dir="vectorstore/client_memory")
    return format_context(chunks)


# Tool schemas in Gemini function-declaration format, used by base_agent.py
TOOL_SCHEMAS = [
    {
        "name": "retrieve_benchmark",
        "description": "Look up an industry benchmark or definition for a KPI metric from curated domain knowledge.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric_name": {"type": "string", "description": "e.g. 'food cost percentage'"},
                "domain": {"type": "string", "description": "'restaurant' or 'ecommerce'"},
            },
            "required": ["metric_name", "domain"],
        },
    },
    {
        "name": "get_kpi_detail",
        "description": "Get the full detail (e.g. monthly breakdown) behind a summary KPI number, or find out why a KPI was skipped.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string"},
                "kpi_name": {"type": "string"},
            },
            "required": ["client_id", "kpi_name"],
        },
    },
    {
        "name": "analyze_sentiment_batch",
        "description": "Run sentiment scoring and theme extraction over a batch of customer review/feedback texts.",
        "parameters": {
            "type": "object",
            "properties": {
                "review_texts": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["review_texts"],
        },
    },
    {
        "name": "query_client_memory",
        "description": "Search this specific client's past computed results and narrative for a follow-up question.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string"},
                "question": {"type": "string"},
            },
            "required": ["client_id", "question"],
        },
    },
]

TOOL_DISPATCH = {
    "retrieve_benchmark": retrieve_benchmark,
    "get_kpi_detail": get_kpi_detail,
    "analyze_sentiment_batch": analyze_sentiment_batch,
    "query_client_memory": query_client_memory,
}
