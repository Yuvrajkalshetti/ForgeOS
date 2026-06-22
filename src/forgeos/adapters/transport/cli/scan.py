"""``forge scan`` — ingest/refresh a repository into the knowledge graph.

Provider-free (ADR 0005). Uses git churn for hotspots when available, otherwise
degrades gracefully.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import typer

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.core.graph import GraphStore
from forgeos.core.repo_intel import RepoIntelEngine
from forgeos.core.repo_intel.hotspots import git_churn


def scan(
    path: Path = Path(),
    project: Path = Path(),
) -> None:
    """Scan ``path`` and store the graph + repo profile under ``project``."""
    db = project / ".forgeos" / "cache" / "forge.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    store = SnapshotStore.open(project / ".forgeos" / "snapshots", db)
    engine = RepoIntelEngine(GraphStore(store), store, churn=git_churn)
    result = engine.scan(path)
    typer.echo(json.dumps(dataclasses.asdict(result), indent=2))
