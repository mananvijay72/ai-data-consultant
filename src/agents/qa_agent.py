"""
qa_agent.py
-----------
Answers follow-up questions after a report has been generated, grounded
in the client's own semantic memory (Phase 6) and, when relevant, the
static domain benchmark corpus (Phase 1). This is the "reuse artifacts as
memory" feature — no new dataset access, purely tool-grounded retrieval.
"""
from src.agents.base_agent import BaseAgent, load_prompt


class QAAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="qa_agent",
            system_prompt=load_prompt("qa_prompt.txt"),
            allowed_tools=["query_client_memory", "retrieve_benchmark"],
        )

    def ask(self, client_id: str, question: str) -> str:
        user_message = f"client_id: {client_id}\nClient question: {question}"
        return self.run(user_message)
