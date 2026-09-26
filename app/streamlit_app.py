"""
streamlit_app.py
------------------
Demo UI: upload a CSV -> run the full pipeline -> view the report inline
with live Plotly charts -> ask follow-up questions in a chat box (backed
by qa_agent.py + the client's semantic memory).

Run with:
    streamlit run app/streamlit_app.py
"""
import os
import sys
import uuid

import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.orchestrator import run_pipeline
from src.report.charts import build_all_charts
from src.agents.qa_agent import QAAgent

st.set_page_config(page_title="Insight Desk", page_icon="📊", layout="wide")
st.title("📊 Insight Desk — AI Data Consultancy (Demo)")
st.caption(
    "Upload a company's raw sales data (restaurant or e-commerce CSV) and get "
    "a consultancy-style report: KPIs, an executive narrative, and product/"
    "customer insights — then ask follow-up questions."
)

if "client_id" not in st.session_state:
    st.session_state.client_id = None
if "report_result" not in st.session_state:
    st.session_state.report_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

uploaded_file = st.file_uploader("Upload client data (CSV)", type=["csv", "xlsx"])

col1, col2 = st.columns([1, 3])
with col1:
    run_clicked = st.button("Run Analysis", type="primary", disabled=uploaded_file is None)

if run_clicked and uploaded_file is not None:
    client_id = f"session_{uuid.uuid4().hex[:8]}"
    tmp_path = os.path.join("data", "clients", "_uploads_tmp")
    os.makedirs(tmp_path, exist_ok=True)
    file_path = os.path.join(tmp_path, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    with st.spinner("Running pipeline: ingest -> classify -> KPIs -> insight -> business -> report..."):
        try:
            result = run_pipeline(file_path, client_id)
            st.session_state.client_id = client_id
            st.session_state.report_result = result
            st.session_state.chat_history = []
            st.success(f"Report generated. Classified as: **{result['domain']}**")
        except Exception as e:
            st.error(f"Pipeline failed: {e}")

if st.session_state.report_result:
    report = st.session_state.report_result["report"]

    st.header(f"Client Report — {report.domain.capitalize()} Business")
    st.caption(f"Generated {report.generated_at} · confidence {report.domain_confidence:.0%}")

    st.subheader("Executive Summary & Insights")
    st.write(report.executive_narrative)

    st.subheader("Key Performance Indicators")
    scalar_kpis = {k: v for k, v in report.kpis.computed.items() if not isinstance(v, dict)}
    kpi_cols = st.columns(min(4, max(1, len(scalar_kpis))))
    for i, (name, value) in enumerate(scalar_kpis.items()):
        with kpi_cols[i % len(kpi_cols)]:
            st.metric(label=name.replace("_", " ").title(), value=value)

    if report.kpis.skipped:
        with st.expander("KPIs not computed (missing data)"):
            for s in report.kpis.skipped:
                st.write(f"**{s['kpi']}** — {s['reason']}")

    charts = build_all_charts(report.kpis.computed)
    if charts:
        st.subheader("Charts")
        for name, fig in charts.items():
            st.plotly_chart(fig, use_container_width=True)

    if report.business_section:
        st.subheader("Product & Customer Insights")
        st.write(report.business_section)

    with open(st.session_state.report_result["pdf_path"], "rb") as f:
        st.download_button("Download PDF Report", f, file_name="client_report.pdf")

    st.divider()
    st.subheader("💬 Ask a follow-up question")
    st.caption("Answered using this client's own results (memory) + industry benchmarks (RAG).")

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(msg)

    question = st.chat_input("e.g. Why did food cost spike, and is that normal?")
    if question:
        st.session_state.chat_history.append(("user", question))
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                qa_agent = QAAgent()
                answer = qa_agent.ask(st.session_state.client_id, question)
                st.write(answer)
        st.session_state.chat_history.append(("assistant", answer))
