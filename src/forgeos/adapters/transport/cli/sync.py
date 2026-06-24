"""``forge sync`` — one-shot: scan + compress + exec-scan + dataflow.

Provider-free and idempotent. Rebuilds the knowledge graph, knowledge cards, and the
code-intelligence graphs (symbols/calls + state reads/writes) in a single step so a
project's ForgeOS state is current. Equivalent to running ``scan``, ``compress run --bulk``,
and ``exec-scan`` in sequence.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import typer

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.core.compression import CardGenerator
from forgeos.core.dataflow_intel import DataFlowEngine, DataFlowStore
from forgeos.core.exec_intel import ExecGraphStore, ExecIntelEngine
from forgeos.core.graph import GraphStore, NodeType
from forgeos.core.repo_intel import RepoIntelEngine
from forgeos.core.repo_intel.hotspots import git_churn


def sync(
    path: Path = Path(),
    project: Path = Path(),
) -> None:
    """Scan + compress + exec-scan + dataflow for ``path``; store under ``project``."""
    store = open_store(project)
    graph = GraphStore(store)
    scan_result = RepoIntelEngine(graph, store, churn=git_churn).scan(path)
    generator = CardGenerator(store, graph)
    cards = [generator.compress(node.id).card_id for node in graph.nodes(NodeType.FILE)]
    exec_result = ExecIntelEngine(ExecGraphStore(store)).scan(path)
    df_result = DataFlowEngine(DataFlowStore(store)).scan(path)
    typer.echo(
        json.dumps(
            {
                "graph": dataclasses.asdict(scan_result),
                "cards": len(cards),
                "exec": dataclasses.asdict(exec_result),
                "dataflow": dataclasses.asdict(df_result),
            },
            indent=2,
            default=str,
        )
    )
