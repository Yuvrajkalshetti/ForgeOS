"""``forge graph`` commands: query and why.

Read-only traversal over the project's knowledge graph. Nodes/edges are produced
by RepoIntel (P4) and other engines; this surfaces them.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.core.graph import GraphStore

graph_app = typer.Typer(help="Inspect the knowledge graph.", no_args_is_help=True)


def _graph(project: Path) -> GraphStore:
    db = project / ".forgeos" / "cache" / "forge.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    store = SnapshotStore.open(project / ".forgeos" / "snapshots", db)
    return GraphStore(store)


def _resolve_id(graph: GraphStore, target: str) -> str | None:
    if graph.get_node(target) is not None:
        return target
    found = graph.find_by_label(target)
    return found.id if found is not None else None


@graph_app.command("query")
def query(
    target: str,
    depth: int = 2,
    project: Path = Path(),
) -> None:
    """Traverse from a node (id or label) and print reachable nodes as JSON."""
    graph = _graph(project)
    node_id = _resolve_id(graph, target)
    if node_id is None:
        typer.echo(json.dumps({"error": f"node not found: {target}"}))
        raise typer.Exit(code=1)
    reachable = graph.traverse(node_id, max_depth=depth)
    typer.echo(
        json.dumps(
            {"start": node_id, "nodes": [n.model_dump(mode="json") for n in reachable]},
            indent=2,
        )
    )


@graph_app.command("why")
def why(target: str, project: Path = Path()) -> None:
    """Print the Decision nodes that explain a node (id or label)."""
    graph = _graph(project)
    decisions = graph.why(target)
    typer.echo(json.dumps([n.model_dump(mode="json") for n in decisions], indent=2))
