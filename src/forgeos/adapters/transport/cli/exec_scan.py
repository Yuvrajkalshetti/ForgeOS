"""``forge exec-scan`` — build the execution + data-flow graphs for a repo.

Provider-free and additive: writes only to the sibling ``exec_*`` / ``df_*`` collections,
never the V1 graph. Python-first; other languages are skipped. Output includes the E5A
resolution statistics that gate E5B.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import typer

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.core.dataflow_intel import DataFlowEngine, DataFlowStore
from forgeos.core.exec_intel import ExecGraphStore, ExecIntelEngine


def exec_scan(
    path: Path = Path(),
    project: Path = Path(),
) -> None:
    """Scan ``path`` for Python symbols/calls + state reads/writes; store under ``project``."""
    store = open_store(project)
    exec_result = ExecIntelEngine(ExecGraphStore(store)).scan(path)
    df_result = DataFlowEngine(DataFlowStore(store)).scan(path)
    out = dataclasses.asdict(exec_result)
    out["dataflow"] = dataclasses.asdict(df_result)
    typer.echo(json.dumps(out, indent=2))
