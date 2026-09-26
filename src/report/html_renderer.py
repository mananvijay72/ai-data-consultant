"""
html_renderer.py
-----------------
Renders a ClientReport (+ charts) into a standalone HTML file using
Jinja2. This HTML file is what pdf_renderer.py converts to PDF, and is
also directly usable as the "dashboard.html" deliverable.
"""
import os
from jinja2 import Environment, FileSystemLoader
from src.report.composer import ClientReport
from src.report.charts import build_all_charts, charts_to_html_divs

TEMPLATE_DIR = "src/report/templates"


def render_html(report: ClientReport, output_path: str) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report_template.html")

    charts = build_all_charts(report.kpis.computed)
    chart_divs = charts_to_html_divs(charts)

    html = template.render(report=report, charts=chart_divs)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)
    return output_path
