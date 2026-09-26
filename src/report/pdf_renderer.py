"""
pdf_renderer.py
----------------
Converts the rendered HTML report into a PDF using WeasyPrint (free,
no headless-browser dependency). Note: WeasyPrint doesn't execute
JavaScript, so the interactive Plotly <script> charts embedded via CDN
won't render in the PDF — for the PDF deliverable we render a
chart-free variant of the template. The interactive HTML dashboard
(html_renderer.py's output) is the one with live Plotly charts.
"""
import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from src.report.composer import ClientReport

TEMPLATE_DIR = "src/report/templates"


def render_pdf(report: ClientReport, output_path: str) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("report_template.html")
    # no charts passed -> template's chart block is simply skipped
    html_string = template.render(report=report, charts={})

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    HTML(string=html_string).write_pdf(output_path)
    return output_path
