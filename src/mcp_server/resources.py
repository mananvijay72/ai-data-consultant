"""
resources.py
------------
MCP "Resource" handlers — passive artifact reads. Thin wrappers around
artifact_store.py, exposed as `artifact://...` URIs on the MCP server.
"""
from typing import Any
from src.memory.artifact_store import read as read_artifact, list_artifacts

RESOURCE_PREFIX = "artifact://"


def list_resources(client_id: str) -> list:
    """Returns the list of artifact:// URIs currently available for a client."""
    return [f"{RESOURCE_PREFIX}{name}" for name in list_artifacts(client_id)]


def read_resource(client_id: str, uri: str) -> Any:
    """
    Reads a resource by its full URI, e.g. 'artifact://kpi/results'.
    Raises FileNotFoundError (via artifact_store.read) if that stage of
    the pipeline hasn't produced it yet — callers should treat that as
    "not ready," not a crash.
    """
    if not uri.startswith(RESOURCE_PREFIX):
        raise ValueError(f"Not an artifact URI: {uri}")
    artifact_name = uri[len(RESOURCE_PREFIX):]
    return read_artifact(client_id, artifact_name)
