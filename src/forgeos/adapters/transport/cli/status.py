"""``forge status`` / ``forgeos status`` — at-a-glance project state.

Read-only operational visibility: what ForgeOS knows about this project and which
provider is active. Counts existing records via the same store/graph the rest of the
CLI uses; introduces no new capability or storage.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.catalog import Collections
from forgeos.config.loader import load_config
from forgeos.core.graph import GraphStore, NodeType

_FORGEOS_DIR = ".forgeos"


def status_cmd(project: Path = Path()) -> None:
    """Print a summary of project knowledge + the active provider as JSON."""
    initialized = (project / _FORGEOS_DIR).exists()
    store = open_store(project)
    graph = GraphStore(store)
    counts = {
        "memory": len(store.query(Collections.MEMORY)),
        "nodes": len(store.query(Collections.NODES)),
        "edges": len(store.query(Collections.EDGES)),
        "cards": len(store.query(Collections.CARDS)),
        "skills": len(graph.nodes(NodeType.SKILL)),
        "proposals": len(store.query(Collections.PROPOSALS)),
        "advisory_sessions": len(store.query(Collections.ADVISORY_SESSIONS)),
    }
    payload = {
        "project": str(project),
        "initialized": initialized,
        "provider": load_config(project_dir=project).providers.default,
        "counts": counts,
    }
    typer.echo(json.dumps(payload, indent=2))
