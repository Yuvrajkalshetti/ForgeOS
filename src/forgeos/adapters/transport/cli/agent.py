"""``forge agent`` commands: run.

Builds the configured provider and runs the orchestrator. If no provider is
available (e.g. missing API key), it fails gracefully — the rest of ForgeOS
(scan/compress/context/memory/graph) keeps working without a provider.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer

from forgeos.adapters.providers import MeteredProvider
from forgeos.adapters.providers.factory import ProviderUnavailable, build_provider
from forgeos.adapters.tokenizer import LocalEstimator
from forgeos.adapters.transport.cli._shared import open_store
from forgeos.config.loader import load_config
from forgeos.config.models import ForgeConfig
from forgeos.core.orchestrator import Orchestrator
from forgeos.core.provider_intel import Router, StatsRecorder
from forgeos.core.token_intel import TokenLedger

agent_app = typer.Typer(help="Run orchestrated agents.", no_args_is_help=True)


def _model_for(config: ForgeConfig) -> str:
    default = config.providers.default
    if default == "claude":
        return config.providers.claude.model
    if default == "ollama":
        return config.providers.ollama.model
    return default


@agent_app.command("run")
def run(task: str, project: Path = Path()) -> None:
    """Run the agent set over a task and print a merged report."""
    store = open_store(project)
    config = load_config(project_dir=project)

    # Routing transparency: explain the selection up front.
    decision = Router(policy="pinned").select(config.providers.default, [config.providers.default])

    try:
        inner = build_provider(config)
    except ProviderUnavailable as exc:
        typer.echo(json.dumps({"routing": decision.model_dump(), "error": str(exc)}, indent=2))
        raise typer.Exit(code=1) from exc

    provider = MeteredProvider(inner, StatsRecorder(store), TokenLedger(store), LocalEstimator())
    orchestrator = Orchestrator(
        provider,
        _model_for(config),
        global_limit=config.concurrency.global_limit,
        per_provider_limit=config.concurrency.per_provider.get(config.providers.default),
    )
    report = asyncio.run(orchestrator.run(task))
    typer.echo(
        json.dumps({"routing": decision.model_dump(), "report": report.model_dump()}, indent=2)
    )
