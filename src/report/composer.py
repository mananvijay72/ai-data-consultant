"""
composer.py
-----------
Merges all published artifacts for a client into a single, validated
report schema (pydantic model), which is then handed to the renderer.
Keeping this as an explicit schema (not a loose dict) means the HTML
template and any future consumer (e.g. an API response) have a contract
that fails loudly if a required piece is missing, rather than silently
rendering a blank section.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from src.memory.artifact_store import read as read_artifact, exists as artifact_exists


class KPISection(BaseModel):
    computed: Dict[str, Any]
    skipped: List[Dict[str, str]]


class ClientReport(BaseModel):
    client_id: str
    domain: str
    domain_confidence: float
    kpis: KPISection
    executive_narrative: str
    business_section: Optional[str] = None
    generated_at: str


def compose_report(client_id: str, generated_at: str) -> ClientReport:
    domain_info = read_artifact(client_id, "dataset/domain_classification")
    kpi_results = read_artifact(client_id, "kpi/results")
    narrative = read_artifact(client_id, "insight/narrative")

    business_section = None
    if artifact_exists(client_id, "business/themes"):
        business_artifact = read_artifact(client_id, "business/themes")
        business_section = business_artifact.get("narrative")

    return ClientReport(
        client_id=client_id,
        domain=domain_info.get("domain", "unknown"),
        domain_confidence=domain_info.get("confidence", 0.0),
        kpis=KPISection(computed=kpi_results.get("computed", {}), skipped=kpi_results.get("skipped", [])),
        executive_narrative=narrative,
        business_section=business_section,
        generated_at=generated_at,
    )
