"""
server.py
---------
A single MCP server exposing both Resources (artifact://...) and Tools
(retrieve_benchmark, get_kpi_detail, analyze_sentiment_batch,
query_client_memory) over stdio, using the official `mcp` Python SDK.

Run standalone for testing:
    python -m src.mcp_server.server

Agents connect to this server as MCP clients (see src/agents/base_agent.py)
so that inter-agent artifact handoff and tool invocation both go through
one consistent protocol instead of direct Python object passing.
"""
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

from src.mcp_server.resources import list_resources, read_resource, RESOURCE_PREFIX
from src.memory.artifact_store import ARTIFACT_NAMES
from src.mcp_server.tools import TOOL_SCHEMAS, TOOL_DISPATCH

app = Server("insight-desk")

# NOTE: MCP resources are technically listed without a client_id in the
# base protocol. For this demo, the server is started per-client-session
# (the orchestrator passes CLIENT_ID as an env var / startup arg) so
# `list_resources`/`read_resource` below close over a single client_id at
# a time. See docs/mcp_spec.md for the simplification rationale.
import os
CLIENT_ID = os.environ.get("INSIGHT_DESK_CLIENT_ID", "demo1")


@app.list_resources()
async def handle_list_resources() -> list[Resource]:
    uris = list_resources(CLIENT_ID)
    return [
        Resource(uri=uri, name=uri.replace(RESOURCE_PREFIX, ""), mimeType="application/json")
        for uri in uris
    ]


@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    content = read_resource(CLIENT_ID, uri)
    return json.dumps(content, default=str)


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(name=schema["name"], description=schema["description"],
             inputSchema=schema["parameters"])
        for schema in TOOL_SCHEMAS
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name not in TOOL_DISPATCH:
        raise ValueError(f"Unknown tool: {name}")
    result = TOOL_DISPATCH[name](**arguments)
    return [TextContent(type="text", text=json.dumps(result, default=str))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
