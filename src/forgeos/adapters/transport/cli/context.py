"""``forge context`` commands: build."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from forgeos.adapters.tokenizer import LocalEstimator
from forgeos.adapters.transport.cli._shared import open_store
from forgeos.config.loader import load_config
from forgeos.core.context_assembly import ContextAssembler
from forgeos.core.graph import GraphStore
from forgeos.core.token_intel import TokenLedger

context_app = typer.Typer(help="Assemble token-budgeted context.", no_args_is_help=True)


@context_app.command("build")
def build(
    target: str,
    depth: int = 2,
    budget: int | None = None,
    source: Path | None = None,
    project: Path = Path(),
) -> None:
    """Assemble a context bundle for a node (id or label) and print it."""
    store = open_store(project)
    config = load_config(project_dir=project)
    limit = budget if budget is not None else (config.tokens.per_request or 8000)
    assembler = ContextAssembler(
        GraphStore(store), LocalEstimator(), store, limit, TokenLedger(store)
    )
    bundle = assembler.build(target, depth=depth, source_root=source)
    typer.echo(json.dumps(bundle.model_dump(), indent=2))
