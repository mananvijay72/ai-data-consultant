"""
base_agent.py
-------------
Shared Gemini client + tool-calling loop used by every agent
(domain_classifier, insight_analyst, business_analyst, qa_agent).

Design: agents call Gemini with a system prompt + tool schemas. If Gemini
requests a tool call, we dispatch it locally (TOOL_DISPATCH from
mcp_server/tools.py — the same functions the MCP server exposes) and feed
the result back, looping until Gemini returns a final text answer.

Note on MCP vs. direct dispatch: in this reference implementation, agents
call tool functions directly (via TOOL_DISPATCH) rather than going through
a live MCP client connection, to keep the demo runnable as a single
process without managing a subprocess/stdio server per request. The MCP
server in src/mcp_server/server.py exposes the *identical* tool schemas
and resource reads, so the same agent code can be pointed at a real MCP
client transport with no change to prompts or dispatch logic — swap
`TOOL_DISPATCH[name](**args)` for `mcp_client.call_tool(name, args)`.
This tradeoff is documented explicitly rather than hidden.
"""
import json
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types as genai_types

from src.config import GEMINI_API_KEY, CONFIG
from src.mcp_server.tools import TOOL_SCHEMAS, TOOL_DISPATCH
from src.memory.artifact_store import read as read_artifact, publish as publish_artifact

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY not set — see .env.example")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _to_gemini_tools(tool_names: List[str]) -> List[dict]:
    schemas = [s for s in TOOL_SCHEMAS if s["name"] in tool_names]
    return [{"function_declarations": schemas}] if schemas else []


class BaseAgent:
    """
    name: agent name, used only for logging.
    system_prompt: loaded from src/agents/prompts/*.txt
    allowed_tools: subset of TOOL_SCHEMAS names this agent may call.
    reads_artifacts / writes_artifact: which MCP-style artifacts this
        agent reads as input context and publishes as output, giving each
        agent an explicit, documented contract (this is the same contract
        the MCP resource layer enforces — see docs/mcp_spec.md).
    """

    def __init__(self, name: str, system_prompt: str, allowed_tools: Optional[List[str]] = None):
        self.name = name
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools or []

    def read_artifact(self, client_id: str, artifact_name: str) -> Any:
        return read_artifact(client_id, artifact_name)

    def publish_artifact(self, client_id: str, artifact_name: str, content: Any) -> None:
        publish_artifact(client_id, artifact_name, content)

    def run(self, user_message: str, max_tool_hops: int = 5) -> str:
        """
        Runs the Gemini tool-calling loop and returns the final text
        response. Raises if the model loops beyond max_tool_hops without
        producing a final answer (defensive against malformed tool loops).
        """
        client = _get_client()
        model = CONFIG["llm"]["model"]
        tools = _to_gemini_tools(self.allowed_tools)

        contents = [
            genai_types.Content(role="user", parts=[genai_types.Part(text=user_message)])
        ]

        for hop in range(max_tool_hops):
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=genai_types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    tools=tools if tools else None,
                    temperature=CONFIG["llm"]["temperature"],
                ),
            )

            candidate = response.candidates[0]
            function_calls = [
                part.function_call for part in candidate.content.parts
                if getattr(part, "function_call", None)
            ]

            if not function_calls:
                # final answer
                text_parts = [p.text for p in candidate.content.parts if getattr(p, "text", None)]
                return "\n".join(text_parts).strip()

            # append the model's turn (including its function call requests)
            contents.append(candidate.content)

            # dispatch each requested tool call and append results
            for fc in function_calls:
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}
                if tool_name not in TOOL_DISPATCH:
                    result = {"error": f"Unknown tool {tool_name}"}
                else:
                    try:
                        result = TOOL_DISPATCH[tool_name](**tool_args)
                    except Exception as e:
                        result = {"error": str(e)}

                contents.append(genai_types.Content(
                    role="tool",
                    parts=[genai_types.Part.from_function_response(
                        name=tool_name, response={"result": result}
                    )],
                ))

        raise RuntimeError(f"{self.name}: exceeded max_tool_hops ({max_tool_hops}) without a final answer")


def load_prompt(filename: str) -> str:
    with open(f"src/agents/prompts/{filename}") as f:
        return f.read()
