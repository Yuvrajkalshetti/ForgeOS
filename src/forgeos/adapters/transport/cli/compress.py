"""``forge compress`` — generate/refresh knowledge cards.

Deterministic and provider-free (ADR 0009): cards are derived from the graph and
RepoProfile, so this works without the provider layer.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.core.compression import CardGenerator
from forgeos.core.graph import GraphStore, NodeType

compress_app = typer.Typer(help="Compress repository knowledge into cards.", no_args_is_help=True)


@compress_app.command("run")
def run(
    target: str | None = None,
    bulk: bool = False,
    project: Path = Path(),
) -> None:
    """Compress a node (``--target NODE``) or all files (``--bulk``)."""
    store = open_store(project)
    graph = GraphStore(store)
    generator = CardGenerator(store, graph)

    if bulk:
        targets = [n.id for n in graph.nodes(NodeType.FILE)]
    elif target is not None:
        targets = [target]
    else:
        raise typer.BadParameter("provide --target NODE or --bulk")

    created = [generator.compress(node_id).card_id for node_id in targets]
    typer.echo(json.dumps({"cards": created}, indent=2))
