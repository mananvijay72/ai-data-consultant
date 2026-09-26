# Architecture

## End-to-end flow

```
CSV upload
   │
   ▼
[Ingestion]  loader.py -> profiler.py -> standardizer.py       (code)
   │  produces: cleaned dataframe, column_map, dataset profile
   ▼
publish to MCP artifact resources: artifact://dataset/*
   │
   ▼
[Domain Classifier Agent]  (Gemini, no tools)                  (LLM)
   │  reads dataset profile + sample rows via MCP resource
   │  outputs: domain label + confidence
   ▼
[KPI Engine]  registry + column-alias resolver                 (code)
   │  computes only KPIs whose required columns resolved
   │  publishes artifact://kpi/results (computed + skipped)
   ▼
[Insight Analyst Agent]  (Gemini + tools: retrieve_benchmark,   (LLM)
   │                      get_kpi_detail)
   │  reads artifact://kpi/results via MCP, calls tools as needed
   │  publishes artifact://insight/narrative
   ▼
[Business Analyst Agent]  (Gemini + tool: analyze_sentiment)   (LLM)
   │  only runs if a review/feedback text column was detected
   │  publishes artifact://business/themes
   ▼
[Report Composer]  merges artifacts -> pydantic schema         (code)
   │  charts.py builds Plotly figures
   │  html_renderer.py + pdf_renderer.py produce final report
   ▼
client_report.pdf + dashboard.html
   │
   ▼
[Memory Indexer]  chunks all artifacts -> embeds ->            (code)
   │               client_{id}_memory Chroma collection
   ▼
[Q&A Agent]  (Gemini + tool: query_client_memory)  <-- follow-up questions
```

## Why only 3 (+1) LLM calls

Domain Classifier, Insight Analyst, Business Analyst, and the on-demand
Q&A Agent. Everything else is deterministic and unit-tested. This is a
deliberate choice: LLMs are used only where the task requires judgment
over ambiguous input (which industry? what does this pattern mean? what
does the user actually want to know?) — not for arithmetic, schema
matching, or chart layout, where deterministic code is cheaper, faster,
and verifiable.

## MCP: resources vs tools

See `docs/mcp_spec.md` for the full table. Short version: **Resources**
are passive artifacts agents read (`artifact://...`), **Tools** are
actions agents decide to invoke (`retrieve_benchmark`, `analyze_sentiment_batch`,
`get_kpi_detail`, `query_client_memory`). Both are served by one MCP
server (`src/mcp_server/server.py`) so every agent is a single MCP client
with access to both primitives.

## Memory: reusing the artifact store

See `docs/memory_design.md`. Structured memory = artifacts as JSON.
Semantic memory = those same artifacts, chunked and embedded into a
per-client Chroma collection, queried with the *same* `retriever.py`
built for the static domain RAG corpus in Phase 1.
