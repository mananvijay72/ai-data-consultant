# MCP Specification

One MCP server (`src/mcp_server/server.py`) exposes both Resources and
Tools. All agents connect as MCP clients.

## Resources (passive artifacts, agent-to-agent handoff)

| URI | Published by | Read by | Content |
|---|---|---|---|
| `artifact://dataset/profile` | Ingestion | Domain Classifier | row count, dtypes, date range, nulls, sample rows |
| `artifact://dataset/cleaned` | Ingestion | KPI Engine | standardized dataframe (parquet, base64) |
| `artifact://dataset/column_map` | Ingestion | KPI Engine, Insight Analyst | canonical -> client column name mapping |
| `artifact://kpi/results` | KPI Engine | Insight Analyst, Business Analyst, Report Composer | `{computed: {...}, skipped: [...]}` |
| `artifact://insight/narrative` | Insight Analyst | Report Composer, Q&A Agent | executive narrative text |
| `artifact://business/themes` | Business Analyst | Report Composer, Q&A Agent | sentiment scores + extracted themes |

## Tools (active, agent-invoked)

| Tool | Used by | Wraps |
|---|---|---|
| `retrieve_benchmark(metric_name, domain)` | Insight Analyst | `src/rag/retriever.py` against domain corpus collection |
| `get_kpi_detail(kpi_name)` | Insight Analyst | reads deeper time-series detail behind a summary KPI number |
| `analyze_sentiment_batch(review_texts)` | Business Analyst | lightweight sentiment scoring + theme extraction |
| `query_client_memory(client_id, question)` | Q&A Agent | `src/rag/retriever.py` against `client_{id}_memory` collection |

## Why one server for both

Keeps every agent's connection code identical (`base_agent.py` connects
once, then calls either `resources/read` or `tools/call`). This mirrors
how a real consultancy team would work: specialists hand off completed
deliverables (resources) but also have shared reference tools they can
pull on demand (tools) — both live on the same "shared drive," not two
separate systems.

## Note on scope

For this demo, the artifact store backing the resources is local disk
(JSON/parquet under `data/clients/{id}/artifacts/`) rather than a live
external system — appropriate since data arrives as batch CSV uploads,
not live external connections. If a "live connector" mode were added
(pulling from a client's own Google Sheet/DB), that is exactly the case
where MCP's value would extend further, since MCP's design goal is
connecting to arbitrary external data sources without hardcoding each
integration.
