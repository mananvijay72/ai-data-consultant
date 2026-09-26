# Insight Desk — AI Data Consultancy (Demo)

Upload a company's raw CSV data and get back a consultancy-style report:
KPIs, an executive narrative, product/customer insights, and a chat box for
follow-up questions — grounded in both static industry knowledge (RAG) and
the client's own computed results (memory).

## Why this architecture (read this before the code)

**Not everything is an "agent."** Only 3 LLM calls exist in the whole
pipeline: Domain Classifier, Insight Analyst, Business Analyst (+ an
on-demand Q&A agent for follow-ups). Everything else — parsing, column
matching, KPI math, chart generation, report rendering — is plain,
testable, deterministic Python. Agents are used only where the task is
genuinely ambiguous (which industry is this? what does this narrative
mean?), because LLM output for arithmetic/lookups is strictly worse than
code and harder to trust.

**Two separate protocols, used for what they're actually good at:**
- **MCP (Model Context Protocol)** — used for *inter-agent data handoff*.
  The Data Engineer step publishes artifacts (cleaned data, KPI results,
  metadata) as MCP **Resources**. Agents read them with `resources/read`
  instead of being tightly coupled to the orchestrator's internal Python
  objects. This makes agents swappable/independently testable.
- **Native tool-calling (Gemini function calling)** — used for *actions* an
  agent decides to take mid-reasoning: `retrieve_benchmark`,
  `analyze_sentiment_batch`, `get_kpi_detail`, `query_client_memory`. These
  are exposed as MCP **Tools** on the same server, so agents are MCP
  clients calling both resources and tools through one connection.

**Memory is not a separate system — it's the artifact store, indexed
twice.** Structured memory (exact facts, e.g. "food_cost_pct = 34.2") lives
as JSON artifacts per client. Semantic memory (for follow-up questions) is
the same artifacts, chunked and embedded into a per-client Chroma
collection. The same `retriever.py` built in Phase 1 for the static
industry RAG corpus is reused, unmodified, to query client memory — it's
just pointed at a different collection.

**KPIs are computed by a registry + column-alias resolver, not an LLM.**
Each domain module declares KPIs with required columns; a resolver maps
the client's actual (messy) column names to canonical names via aliases.
KPIs whose required columns aren't present are honestly reported as
"skipped," not hallucinated. See `src/kpi_engine/base.py`.

## Stack

| Layer | Choice |
|---|---|
| LLM | Gemini 2.5 Flash (function calling) |
| Embeddings | Gemini `text-embedding-004` |
| Vector store | ChromaDB (local, persistent) |
| Inter-agent bus | MCP (resources + tools) |
| Dashboard/charts | Plotly |
| Report | Jinja2 → HTML → WeasyPrint → PDF |
| Memory | SQLite (artifact index) + Chroma (per-client semantic memory) |
| Demo UI | Streamlit |

## Build phases

1. **RAG** (`src/rag/`) — standalone, tested in isolation first.
2. **Deterministic core** (`src/ingestion/`, `src/kpi_engine/`).
3. **MCP server** (`src/mcp_server/`) — resources + tools.
4. **Agents** (`src/agents/`) — Gemini + tool-calling + MCP client.
5. **Report** (`src/report/`) — composer, charts, HTML/PDF.
6. **Memory + follow-up Q&A** (`src/memory/`, `qa_agent.py`).
7. **Streamlit app** (`app/streamlit_app.py`).

See `docs/architecture.md`, `docs/mcp_spec.md`, `docs/memory_design.md` for
details on each.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your GEMINI_API_KEY (free at aistudio.google.com)

# Phase 1: build the RAG corpus into Chroma
python -m src.rag.cli build --domain restaurant
python -m src.rag.cli build --domain ecommerce
python -m src.rag.cli query --domain restaurant --q "what is a healthy food cost percentage?"

# Full pipeline (once later phases are wired)
python -m src.orchestrator --file data/samples/restaurant_sales_sample.csv --client_id demo1

# Streamlit demo
streamlit run app/streamlit_app.py
```
