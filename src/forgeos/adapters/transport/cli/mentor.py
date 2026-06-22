"""``forge mentor`` — pre-execution advisory (Mentor), ForgeOS-grounded (P6.6).

Provider-backed; fails gracefully when no provider is configured. Mentor consumes a
deterministic, budgeted ContextBundle (cards, memory, ADRs, repo profile, decisions,
past findings). It never executes or approves.
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
from forgeos.core.advisory import AdvisoryContextBuilder, AdvisorySessionStore, Mentor
from forgeos.core.context_assembly.models import ContextBundle
from forgeos.core.graph import GraphStore
from forgeos.core.memory import MemoryService
from forgeos.core.provider_intel import StatsRecorder
from forgeos.core.token_intel import TokenLedger


def mentor(
    request: str,
    target: list[str] | None = None,
    depth: int = 2,
    budget: int | None = None,
    adr_dir: Path | None = None,
    source: bool = typer.Option(False, "--source", help="allow raw source escalation"),
    ground: bool = typer.Option(True, "--ground/--no-ground"),
    json_out: bool = typer.Option(False, "--json"),
    project: Path = Path(),
) -> None:
    """Ask Mentor for an implementation strategy, grounded in ForgeOS knowledge."""
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
        adr = adr_dir if adr_dir is not None else project / "docs" / "adr"
        builder = AdvisoryContextBuilder(
            graph, store, MemoryService(store), LocalEstimator(), TokenLedger(store)
        )
        grounding = builder.for_mentor(
            target[0] if target else request,
            budget=budget if budget is not None else (config.tokens.per_request or 8000),
            depth=depth,
            adr_dir=adr if adr.is_dir() else None,
            allow_source=source,
            source_root=project,
        )

    rec = asyncio.run(
        Mentor(provider, graph).advise(
            request, model=provider_model(config), grounding=grounding, targets=target
        )
    )
    session = AdvisorySessionStore(store).start(request, rec.id)
    if json_out:
        typer.echo(
            json.dumps(
                {
                    "recommendation": rec.model_dump(),
                    "session_id": session.id,
                    "grounding": grounding.model_dump() if grounding else None,
                },
                indent=2,
            )
        )
    else:
        typer.echo(rec.to_markdown())
        typer.echo(f"\n(session: {session.id}; grounded items: {len(rec.grounding_refs)})")
