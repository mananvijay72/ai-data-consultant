"""
retriever.py
------------
Generic semantic retrieval over any Chroma collection. This same function
is used for:
  - the static domain corpus (collection_name="restaurant"/"ecommerce")
  - per-client semantic memory (collection_name="client_{id}_memory")

Keeping this generic (no domain-specific logic) is what lets "memory"
in Phase 6 be a reuse of Phase 1's RAG code rather than a new system.
"""
from dataclasses import dataclass
from typing import List
from src.config import CONFIG
from src.rag.indexer import get_client
from src.rag.embedder import embed_query


@dataclass
class RetrievedChunk:
    text: str
    source: str
    distance: float


def query(collection_name: str, question: str, top_k: int = None,
          persist_dir: str = None) -> List[RetrievedChunk]:
    top_k = top_k or CONFIG["rag"]["top_k"]
    client = get_client(persist_dir)
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        raise ValueError(
            f"Collection '{collection_name}' does not exist. "
            f"Build it first (see src/rag/cli.py)."
        ) from e

    query_embedding = embed_query(question)
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    chunks = []
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]
    for doc, meta, dist in zip(docs, metas, dists):
        chunks.append(RetrievedChunk(
            text=doc,
            source=meta.get("source_file", meta.get("source", "unknown")),
            distance=dist,
        ))
    return chunks


def format_context(chunks: List[RetrievedChunk]) -> str:
    """Formats retrieved chunks into a context block suitable for prompting."""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[{i}] (source: {c.source})\n{c.text}")
    return "\n\n".join(parts)
