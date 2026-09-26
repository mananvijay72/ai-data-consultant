"""
artifact_store.py
------------------
The backing storage for pipeline artifacts, per client. This is
"structured memory" (§a in docs/memory_design.md) — exact JSON facts,
keyed by URI, no embeddings involved.

Layout on disk:
    data/clients/{client_id}/artifacts/{artifact_name}.json
    data/clients/{client_id}/raw_upload.csv

The MCP server's resource handlers (src/mcp_server/resources.py) read
through this module rather than touching disk directly, so the storage
backend could later be swapped (e.g. to SQLite or a real DB) without
changing MCP resource definitions.
"""
import json
import os
from typing import Any, Dict, List

CLIENTS_DIR = "data/clients"

# canonical artifact names -> filename (also doubles as the MCP resource
# URI suffix, e.g. "dataset/profile" -> artifact://dataset/profile)
ARTIFACT_NAMES = [
    "dataset/profile",
    "dataset/column_map",
    "dataset/domain_classification",
    "kpi/results",
    "insight/narrative",
    "business/themes",
]


def _artifact_path(client_id: str, artifact_name: str) -> str:
    safe_name = artifact_name.replace("/", "__")
    client_dir = os.path.join(CLIENTS_DIR, client_id, "artifacts")
    os.makedirs(client_dir, exist_ok=True)
    return os.path.join(client_dir, f"{safe_name}.json")


def publish(client_id: str, artifact_name: str, content: Any) -> None:
    """Writes an artifact (any JSON-serializable content) for a client."""
    path = _artifact_path(client_id, artifact_name)
    with open(path, "w") as f:
        json.dump(content, f, indent=2, default=str)


def read(client_id: str, artifact_name: str) -> Any:
    path = _artifact_path(client_id, artifact_name)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Artifact '{artifact_name}' not found for client '{client_id}'. "
            f"Has the pipeline stage that produces it run yet?"
        )
    with open(path) as f:
        return json.load(f)


def exists(client_id: str, artifact_name: str) -> bool:
    return os.path.exists(_artifact_path(client_id, artifact_name))


def list_artifacts(client_id: str) -> List[str]:
    return [name for name in ARTIFACT_NAMES if exists(client_id, name)]


def read_all(client_id: str) -> Dict[str, Any]:
    return {name: read(client_id, name) for name in list_artifacts(client_id)}
