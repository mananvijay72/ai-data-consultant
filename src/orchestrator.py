"""
orchestrator.py
-----------------
Runs the full pipeline for one client, end to end:

  ingest -> profile -> classify domain -> run KPI engine -> insight agent
  -> business agent -> compose report -> render HTML+PDF -> index memory

Usage:
    python -m src.orchestrator --file data/samples/restaurant_sales_sample.csv --client_id demo1
"""
import argparse
import os
import shutil
from datetime import datetime, timezone

from src.ingestion.loader import load_file
from src.ingestion.profiler import profile_dataset
from src.kpi_engine.base import run_kpi_engine
from src.kpi_engine.restaurant import REGISTRY as RESTAURANT_REGISTRY
from src.kpi_engine.ecommerce import REGISTRY as ECOMMERCE_REGISTRY
from src.memory.artifact_store import publish as publish_artifact
from src.memory.memory_indexer import build_client_memory
from src.agents.domain_classifier import DomainClassifierAgent
from src.agents.insight_analyst import InsightAnalystAgent
from src.agents.business_analyst import BusinessAnalystAgent
from src.report.composer import compose_report
from src.report.html_renderer import render_html
from src.report.pdf_renderer import render_pdf

REGISTRIES = {
    "restaurant": RESTAURANT_REGISTRY,
    "ecommerce": ECOMMERCE_REGISTRY,
}


def run_pipeline(file_path: str, client_id: str) -> dict:
    client_dir = os.path.join("data", "clients", client_id)
    os.makedirs(client_dir, exist_ok=True)
    raw_copy_path = os.path.join(client_dir, "raw_upload" + os.path.splitext(file_path)[1])
    shutil.copy(file_path, raw_copy_path)

    # 1. Ingestion (code)
    print(f"[1/6] Loading and profiling {file_path}...")
    df = load_file(file_path)
    profile = profile_dataset(df)
    publish_artifact(client_id, "dataset/profile", profile)

    # 2. Domain Classifier (LLM)
    print("[2/6] Classifying domain...")
    classifier = DomainClassifierAgent()
    classification = classifier.classify(client_id)
    domain = classification["domain"]
    print(f"      -> domain: {domain} (confidence {classification['confidence']})")

    if domain not in REGISTRIES:
        raise ValueError(
            f"Domain '{domain}' is not supported yet (supported: {list(REGISTRIES)}). "
            f"Classifier reasoning: {classification.get('reasoning')}"
        )

    # 3. KPI Engine (code)
    print("[3/6] Running KPI engine...")
    kpi_result = run_kpi_engine(df, REGISTRIES[domain])
    publish_artifact(client_id, "kpi/results", kpi_result)
    publish_artifact(client_id, "dataset/column_map", kpi_result["column_map"])
    print(f"      -> computed {len(kpi_result['computed'])} KPIs, "
          f"skipped {len(kpi_result['skipped'])}")

    # 4. Insight Analyst (LLM + tools)
    print("[4/6] Writing insight narrative...")
    insight_agent = InsightAnalystAgent()
    insight_agent.write_narrative(client_id, domain)

    # 5. Business Analyst (LLM + tool), only if a text column was detected
    print("[5/6] Writing business/customer-feedback section...")
    review_texts = None
    text_col = profile.get("detected_text_column")
    if text_col and text_col in df.columns:
        review_texts = df[text_col].dropna().astype(str).tolist()
    business_agent = BusinessAnalystAgent()
    business_agent.write_business_section(client_id, review_texts)

    # 6. Compose + render report
    print("[6/6] Composing and rendering report...")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = compose_report(client_id, generated_at)

    html_path = os.path.join(client_dir, "dashboard.html")
    pdf_path = os.path.join(client_dir, "client_report.pdf")
    render_html(report, html_path)
    render_pdf(report, pdf_path)

    # Build semantic memory for follow-up Q&A (Phase 6)
    n_snippets = build_client_memory(client_id)
    print(f"      -> indexed {n_snippets} memory snippets for follow-up Q&A")

    print(f"\nDone. Outputs:\n  {html_path}\n  {pdf_path}")
    return {"html_path": html_path, "pdf_path": pdf_path, "domain": domain, "report": report}


def main():
    parser = argparse.ArgumentParser(description="Run the Insight Desk pipeline for one client")
    parser.add_argument("--file", required=True, help="Path to client CSV/XLSX")
    parser.add_argument("--client_id", required=True, help="Client identifier (used for storage paths)")
    args = parser.parse_args()
    run_pipeline(args.file, args.client_id)


if __name__ == "__main__":
    main()
