"""``forge tokens`` commands: report."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.core.token_intel import TokenLedger

tokens_app = typer.Typer(help="Token usage and savings.", no_args_is_help=True)


@tokens_app.command("report")
def report(project: Path = Path()) -> None:
    """Print aggregated token savings as JSON."""
    ledger = TokenLedger(open_store(project))
    typer.echo(json.dumps(ledger.report().model_dump(), indent=2))
