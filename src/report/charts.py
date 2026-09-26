"""
charts.py
---------
Builds Plotly figures from the KPI Engine's computed output. Returns
figures both as embeddable HTML div strings (for the report) and can be
reused directly in Streamlit (Phase 7), since both consume the same
Plotly figure objects.
"""
from typing import Any, Dict, List, Optional
import plotly.graph_objects as go
import plotly.io as pio


def revenue_trend_chart(monthly_trend: Dict[str, float]) -> go.Figure:
    months = list(monthly_trend.keys())
    values = list(monthly_trend.values())
    fig = go.Figure(data=go.Scatter(x=months, y=values, mode="lines+markers", line=dict(width=3)))
    fig.update_layout(title="Revenue Trend (Monthly)", xaxis_title="Month", yaxis_title="Revenue",
                       template="plotly_white", height=400)
    return fig


def top_n_bar_chart(data: Dict[str, float], title: str) -> go.Figure:
    labels = list(data.keys())
    values = list(data.values())
    fig = go.Figure(data=go.Bar(x=labels, y=values))
    fig.update_layout(title=title, xaxis_title="", yaxis_title="Revenue", template="plotly_white", height=400)
    return fig


def build_all_charts(computed_kpis: Dict[str, Any]) -> Dict[str, go.Figure]:
    """
    Only builds charts for KPIs that were actually computed — mirrors the
    KPI Engine's "skip gracefully" philosophy at the visualization layer.
    """
    charts = {}
    if "revenue_trend_monthly" in computed_kpis:
        charts["revenue_trend"] = revenue_trend_chart(computed_kpis["revenue_trend_monthly"])

    for key in ("top_selling_items", "top_selling_products"):
        if key in computed_kpis:
            charts["top_items"] = top_n_bar_chart(computed_kpis[key], "Top Performers by Revenue")

    for key in ("bottom_selling_items", "bottom_selling_products"):
        if key in computed_kpis:
            charts["bottom_items"] = top_n_bar_chart(computed_kpis[key], "Lowest Performers by Revenue")

    return charts


def charts_to_html_divs(charts: Dict[str, go.Figure]) -> Dict[str, str]:
    """Converts figures to standalone HTML <div> strings for embedding in the Jinja2 template."""
    return {
        name: pio.to_html(fig, include_plotlyjs=False, full_html=False, div_id=name)
        for name, fig in charts.items()
    }
