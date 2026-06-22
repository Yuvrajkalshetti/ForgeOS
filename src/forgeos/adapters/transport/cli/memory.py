"""``forge memory`` commands: add, query, gc.

A transport adapter over :class:`MemoryService` + :class:`LifecycleManager`,
backed by the snapshot store under ``<project>/.forgeos``.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import typer

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.core.memory import (
    LifecycleManager,
    MemoryKind,
    MemoryScope,
    MemoryService,
)
from forgeos.core.memory.models import Source, utcnow

memory_app = typer.Typer(help="Manage memory records.", no_args_is_help=True)


def _open(project: Path) -> tuple[MemoryService, SnapshotStore]:
    db = project / ".forgeos" / "cache" / "forge.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    store = SnapshotStore.open(project / ".forgeos" / "snapshots", db)
    return MemoryService(store), store


@memory_app.command("add")
def add(
    content: str,
    scope: MemoryScope = MemoryScope.PROJECT,
    kind: MemoryKind = MemoryKind.FACT,
    ref: str | None = None,
    ttl: int | None = None,
    project: Path = Path(),
) -> None:
    """Add a memory record and print its id."""
    service, _ = _open(project)
    record = service.add(
        scope, kind, content, source=Source(type="cli", ref=ref), ttl_seconds=ttl
    )
    typer.echo(record.id)


@memory_app.command("query")
def query(
    scope: MemoryScope | None = None,
    kind: MemoryKind | None = None,
    project: Path = Path(),
) -> None:
    """Print matching memory records as JSON (newest first)."""
    service, _ = _open(project)
    records = service.query(scope=scope, kind=kind)
    typer.echo(json.dumps([r.model_dump(mode="json") for r in records], indent=2))


@memory_app.command("gc")
def gc(project: Path = Path()) -> None:
    """Run a lifecycle pass (expire/decay/propose) and print the report."""
    service, store = _open(project)
    report = LifecycleManager(service, store).gc(utcnow())
    typer.echo(json.dumps(dataclasses.asdict(report), indent=2))
