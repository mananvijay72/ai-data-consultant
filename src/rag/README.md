# RAG Module

Standalone retrieval-augmented-generation layer. No dependency on agents,
MCP, or the pipeline — build and test this first.

## Files

- `embedder.py` — wraps Gemini's embedding API (`text-embedding-004`).
- `chunker.py` — splits markdown docs into overlapping word-chunks.
- `indexer.py` — reads a folder of `.md` docs, chunks + embeds them, writes
  to a persistent Chroma collection (one collection per domain).
- `retriever.py` — generic `.query(collection_name, text, top_k)` used both
  for the static domain corpus AND (in Phase 6) per-client memory
  collections. This reuse is intentional — see `docs/memory_design.md`.
- `cli.py` — command-line entry point: `build` and `query`.

## Usage

```bash
python -m src.rag.cli build --domain restaurant
python -m src.rag.cli build --domain ecommerce
python -m src.rag.cli query --domain restaurant --q "healthy food cost percentage"
```

## Design notes

- Chunking is paragraph-aware (splits on blank lines first, then packs
  paragraphs up to `chunk_size` words with `chunk_overlap` overlap) rather
  than a naive fixed-character split, so chunks don't cut sentences in
  half — important for a 15-20 doc corpus where every chunk's quality
  matters.
- Each Chroma collection is named after the domain (`restaurant`,
  `ecommerce`) for the static corpus, and `client_{client_id}_memory` for
  per-client semantic memory (Phase 6) — same retriever code, different
  collection name.
