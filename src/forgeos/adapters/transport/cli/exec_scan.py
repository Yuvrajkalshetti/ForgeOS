"""``forge exec-scan`` — index Python symbols into the execution graph (E1, ADR 0015).

Provider-free and additive: writes only to the sibling ``exec_nodes``/``exec_edges``
collections, never the V1 ``nodes``/``edges`` graph. Python-first; other languages are
skipped by the engine.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import typer

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.core.exec_intel import ExecGraphStore, ExecIntelEngine


def exec_scan(
    path: Path = Path(),
    project: Path = Path(),
) -> None:
    """Scan ``path`` for Python symbols; store them under ``project``/.forgeos."""
    store = open_store(project)
    engine = ExecIntelEngine(ExecGraphStore(store))
    result = engine.scan(path)
    typer.echo(json.dumps(dataclasses.asdict(result), indent=2))
