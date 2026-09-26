"""
business_analyst.py
--------------------
Writes the product/customer-feedback section. Only calls the sentiment
tool when a review/feedback text column was actually detected in the
dataset (see profiler.py's _detect_text_column) — otherwise it just
narrates product performance from the KPI data already computed.
"""
import json
from typing import List, Optional
from src.agents.base_agent import BaseAgent, load_prompt


class BusinessAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="business_analyst",
            system_prompt=load_prompt("business_prompt.txt"),
            allowed_tools=["analyze_sentiment_batch"],
        )

    def write_business_section(self, client_id: str, review_texts: Optional[List[str]] = None) -> str:
        kpi_results = self.read_artifact(client_id, "kpi/results")

        message_parts = [
            f"client_id: {client_id}",
            f"KPI results (for product/category performance context):\n"
            f"{json.dumps(kpi_results, indent=2, default=str)}",
        ]
        if review_texts:
            sample = review_texts[:200]  # cap for prompt size in this demo
            message_parts.append(
                f"Sample of {len(sample)} customer review/feedback texts is available. "
                f"Call analyze_sentiment_batch with these texts before writing about sentiment:\n"
                f"{json.dumps(sample)}"
            )
        else:
            message_parts.append(
                "No review/feedback text column was detected in this dataset — "
                "do not call analyze_sentiment_batch, just cover product performance."
            )

        narrative = self.run("\n\n".join(message_parts))

        themes_artifact = {"narrative": narrative, "had_review_data": bool(review_texts)}
        self.publish_artifact(client_id, "business/themes", themes_artifact)
        return narrative
