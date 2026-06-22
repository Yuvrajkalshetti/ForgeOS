"""``forge skill`` commands: list, show (minimal Skill capability).

Read-only inspection of Skill nodes created by approved Learning commits. The full
Skill Graph (lifecycle/versioning/search/invocation) is deferred to V2 (ADR 0012).
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.core.graph import GraphStore, NodeType

skill_app = typer.Typer(
    help="Inspect skills (created via approved learning).", no_args_is_help=True
)


def _graph(project: Path) -> GraphStore:
    db = project / ".forgeos" / "cache" / "forge.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    return GraphStore(SnapshotStore.open(project / ".forgeos" / "snapshots", db))


@skill_app.command("list")
def list_skills(project: Path = Path()) -> None:
    """List all Skill nodes as JSON."""
    skills = _graph(project).nodes(NodeType.SKILL)
    typer.echo(json.dumps([s.model_dump(mode="json") for s in skills], indent=2))


@skill_app.command("show")
def show(target: str, project: Path = Path()) -> None:
    """Show one Skill node (by id or label), including lineage in props."""
    graph = _graph(project)
    node = graph.get_node(target) or graph.find_by_label(target)
    if node is None or node.type is not NodeType.SKILL:
        typer.echo(json.dumps({"error": f"skill not found: {target}"}))
        raise typer.Exit(code=1)
    typer.echo(json.dumps(node.model_dump(mode="json"), indent=2))
