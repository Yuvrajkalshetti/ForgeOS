"""``forge audit`` — post-hoc advisory (Auditor), ForgeOS-grounded (P6.6).

Provider-backed; fails gracefully when no provider is configured. Auditor consumes a
budgeted ContextBundle (acceptance criteria, decisions, past findings, cards,
evidence). It never executes or approves.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer

from forgeos.adapters.providers import MeteredProvider
from forgeos.adapters.providers.factory import ProviderUnavailable, build_provider
from forgeos.adapters.tokenizer import LocalEstimator
from forgeos.adapters.transport.cli._shared import open_store, provider_model
from forgeos.config.loader import load_config
from forgeos.core.advisory import AdvisoryContextBuilder, AdvisorySessionStore, Auditor
from forgeos.core.context_assembly.models import ContextBundle
from forgeos.core.graph import GraphStore
from forgeos.core.memory import MemoryService
from forgeos.core.provider_intel import StatsRecorder
from forgeos.core.token_intel import TokenLedger


def audit(
    scope: str,
    criteria: str = "",
    evidence: str = "",
    session: str | None = None,
    target: list[str] | None = None,
    depth: int = 2,
    budget: int | None = None,
    ground: bool = typer.Option(True, "--ground/--no-ground"),
    json_out: bool = typer.Option(False, "--json"),
    project: Path = Path(),
) -> None:
    """Ask Auditor to validate a scope against evidence, grounded in ForgeOS knowledge."""
    store = open_store(project)
    config = load_config(project_dir=project)
    try:
        inner = build_provider(config)
    except ProviderUnavailable as exc:
        typer.echo(json.dumps({"error": str(exc)}))
        raise typer.Exit(code=1) from exc

    provider = MeteredProvider(inner, StatsRecorder(store), TokenLedger(store), LocalEstimator())
    graph = GraphStore(store)
    grounding: ContextBundle | None = None
    if ground:
        builder = AdvisoryContextBuilder(
            graph, store, MemoryService(store), LocalEstimator(), TokenLedger(store)
        )
        grounding = builder.for_auditor(
            target[0] if target else scope,
            budget=budget if budget is not None else (config.tokens.per_request or 8000),
            criteria=criteria,
            evidence=evidence,
            depth=depth,
        )

    finding = asyncio.run(
        Auditor(provider, graph).audit(
            scope, model=provider_model(config), evidence=evidence,
            grounding=grounding, targets=target,
        )
    )
    if session is not None:
        AdvisorySessionStore(store).attach(session, finding_id=finding.id)
    if json_out:
        typer.echo(
            json.dumps(
                {
                    "finding": finding.model_dump(),
                    "grounding": grounding.model_dump() if grounding else None,
                },
                indent=2,
            )
        )
    else:
        typer.echo(finding.to_markdown())
