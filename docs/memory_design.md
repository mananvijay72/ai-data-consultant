# Memory Design

Two kinds of memory. Don't conflate them.

## a) Structured memory (facts)

The pipeline artifacts themselves — `artifact://kpi/results`,
`artifact://insight/narrative`, `artifact://business/themes` — stored as
JSON files per client under `data/clients/{client_id}/artifacts/`, indexed
in a small SQLite table (`src/memory/artifact_store.py`) for exact/keyed
lookup: "give me the KPI results for client 42." No embeddings involved.

## b) Semantic memory (follow-up Q&A)

When a client asks a free-form follow-up question after the report is
generated ("why did food cost spike in March?"), exact key lookup isn't
enough — the question needs to be matched against relevant *content*
inside the artifacts. So:

1. `memory_indexer.py` chunks the structured artifacts (narrative
   paragraphs, KPI number + label pairs, review themes) into short text
   snippets.
2. Each snippet is embedded (same `embedder.py` from Phase 1) and written
   into a **per-client Chroma collection** named `client_{id}_memory` —
   completely separate from the static domain corpus collections.
3. `qa_agent.py` retrieves from *both* collections for a follow-up
   question: the client's own memory collection (their specific numbers)
   and the static domain corpus (industry benchmarks/definitions), then
   answers grounded in both.

## Why this is "free" once RAG exists

`retriever.py`'s `query(collection_name, question, top_k)` function is
completely generic — it doesn't know or care whether `collection_name` is
`"restaurant"` (static corpus) or `"client_42_memory"` (semantic memory).
Building memory is therefore not a new retrieval system, it's:
- a new *indexer* that chunks JSON artifacts instead of markdown files
  (`memory_indexer.py`, ~40 lines, reuses `embedder.py` and
  `indexer.add_texts_to_collection`)
- a new *agent* that queries two collections instead of one
  (`qa_agent.py`)

This is why Phase 1 (build RAG generically, test it standalone) pays off
directly in Phase 6.
