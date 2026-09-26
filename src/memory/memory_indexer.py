"""
memory_indexer.py
------------------
Builds a per-client SEMANTIC memory collection (§b in
docs/memory_design.md) from that client's structured artifacts. This is
the piece that turns "we stored the report" into "we can answer follow-up
questions about the report" — and it deliberately reuses Phase 1's
embedder + indexer code rather than building a new retrieval system.

Run this once, right after the report pipeline finishes for a client.
"""
from typing import Any, Dict, List
from src.memory.artifact_store import read_all
from src.rag.indexer import add_texts_to_collection

CLIENT_MEMORY_DIR = "vectorstore/client_memory"  # separate persist dir from domain corpus


def _artifacts_to_snippets(client_id: str, artifacts: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Flattens structured JSON artifacts into short, retrievable text
    snippets. Each snippet keeps a pointer back to which artifact it came
    from (useful for citing "according to your KPI results..." in answers).
    """
    snippets = []

    kpi = artifacts.get("kpi/results", {})
    for name, value in kpi.get("computed", {}).items():
        snippets.append({
            "text": f"KPI '{name}' = {value}",
            "artifact": "kpi/results",
        })
    for skipped in kpi.get("skipped", []):
        snippets.append({
            "text": f"KPI '{skipped['kpi']}' could not be computed: {skipped['reason']}",
            "artifact": "kpi/results",
        })

    narrative = artifacts.get("insight/narrative")
    if narrative:
        # split narrative into paragraphs so each is independently retrievable
        for i, para in enumerate(str(narrative).split("\n\n")):
            if para.strip():
                snippets.append({"text": para.strip(), "artifact": f"insight/narrative#{i}"})

    themes = artifacts.get("business/themes", {})
    for theme in themes.get("themes", []):
        snippets.append({
            "text": f"Customer feedback theme: {theme}",
            "artifact": "business/themes",
        })

    return snippets


def build_client_memory(client_id: str) -> int:
    artifacts = read_all(client_id)
    snippets = _artifacts_to_snippets(client_id, artifacts)
    if not snippets:
        return 0

    texts = [s["text"] for s in snippets]
    metadatas = [{"source": s["artifact"]} for s in snippets]
    ids = [f"{client_id}::{i}" for i in range(len(snippets))]

    collection_name = f"client_{client_id}_memory"
    add_texts_to_collection(
        collection_name=collection_name,
        texts=texts,
        metadatas=metadatas,
        ids=ids,
        persist_dir=CLIENT_MEMORY_DIR,
    )
    return len(snippets)
