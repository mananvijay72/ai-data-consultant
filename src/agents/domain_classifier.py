"""
domain_classifier.py
---------------------
The only agent with no tools — it reasons purely over the dataset profile
(artifact://dataset/profile) and outputs a domain label. Kept tool-free
deliberately: classification from a profile + sample rows is a pure
reasoning task with nothing external to look up.
"""
import json
from typing import Any, Dict
from src.agents.base_agent import BaseAgent, load_prompt


class DomainClassifierAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="domain_classifier",
            system_prompt=load_prompt("classifier_prompt.txt"),
            allowed_tools=[],
        )

    def classify(self, client_id: str) -> Dict[str, Any]:
        profile = self.read_artifact(client_id, "dataset/profile")
        user_message = f"Dataset profile:\n{json.dumps(profile, indent=2, default=str)}"
        raw_response = self.run(user_message)

        try:
            # strip markdown code fences if the model added them anyway
            cleaned = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            result = {"domain": "unknown", "confidence": 0.0,
                      "reasoning": f"Could not parse model output: {raw_response!r}"}

        self.publish_artifact(client_id, "dataset/domain_classification", result)
        return result
