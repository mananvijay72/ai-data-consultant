# Getting Started / Build Checklist

## 0. Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# add GEMINI_API_KEY from https://aistudio.google.com/apikey (free tier)
```

## 1. Verify the deterministic core first (no API key needed)

```bash
pytest tests/unit/test_chunker.py -v
pytest tests/unit/test_column_resolver.py -v
pytest tests/unit/test_kpi_engine.py -v
```

These confirm chunking, column-alias resolution, and KPI computation all
work correctly against the bundled sample datasets
(`data/samples/restaurant_sales_sample.csv`,
`data/samples/ecommerce_orders_sample.csv`) — already verified during
development.

## 2. Build the RAG corpus (needs GEMINI_API_KEY)

```bash
python -m src.rag.cli build --domain restaurant
python -m src.rag.cli build --domain ecommerce
python -m src.rag.cli query --domain restaurant --q "healthy food cost percentage"
python -m src.evaluation.eval_rag_retrieval
```

## 3. Run the full pipeline for a sample client

```bash
python -m src.orchestrator --file data/samples/restaurant_sales_sample.csv --client_id demo1
python -m src.orchestrator --file data/samples/ecommerce_orders_sample.csv --client_id demo2
```

Outputs land in `data/clients/{client_id}/dashboard.html` and
`client_report.pdf`.

## 4. Run the Streamlit demo

```bash
streamlit run app/streamlit_app.py
```

Upload one of the sample CSVs, run the analysis, view the report, and ask
a follow-up question in the chat box at the bottom.

## 5. Run the full test suite

```bash
pytest tests/ -v
```

Tests that require the Gemini API (RAG retrieval, full pipeline, memory
Q&A) are automatically skipped if `GEMINI_API_KEY` is not set, and run
normally if it is.

## Known environment note

This repo was scaffolded and its deterministic logic (chunker, column
resolver, KPI engine) validated in a sandboxed environment without
outbound network access, so `chromadb`/`google-genai`-dependent code paths
(RAG indexing/retrieval, all LLM agent calls) could not be executed there
and should be your first thing to test once you have a working internet
connection and API key.
