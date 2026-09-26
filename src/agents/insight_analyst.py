"""
insight_analyst.py
--------------------
Writes the KPI narrative / executive summary section. Has tools to look
up benchmarks and drill into KPI detail — this is the agent where
tool-calling earns its place: it decides, per KPI, whether it needs
grounding before commenting.
"""
import json
from src.agents.base_agent import BaseAgent, load_prompt


class InsightAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="insight_analyst",
            system_prompt=load_prompt("insight_prompt.txt"),
            allowed_tools=["retrieve_benchmark", "get_kpi_detail"],
        )

    def write_narrative(self, client_id: str, domain: str) -> str:
        kpi_results = self.read_artifact(client_id, "kpi/results")
        user_message = (
            f"client_id: {client_id}\n"
            f"domain: {domain}\n"
            f"KPI results:\n{json.dumps(kpi_results, indent=2, default=str)}\n\n"
            f"Write the executive summary and KPI narrative section now."
        )
        narrative = self.run(user_message)
        self.publish_artifact(client_id, "insight/narrative", narrative)
        return narrative
