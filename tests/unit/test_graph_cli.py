from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.adapters.transport.cli.app import app
from forgeos.core.graph import EdgeType, GraphStore, NodeType

runner = CliRunner()


def _seed(project: Path) -> None:
    db = project / ".forgeos" / "cache" / "forge.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    graph = GraphStore(SnapshotStore.open(project / ".forgeos" / "snapshots", db))
    graph.upsert_node(NodeType.MODULE, "auth", node_id="auth")
    graph.upsert_node(NodeType.FILE, "auth/main.py", node_id="f1")
    graph.upsert_node(NodeType.DECISION, "use jwt", node_id="dec1")
    graph.add_edge("auth", "f1", EdgeType.CONTAINS)
    graph.add_edge("auth", "dec1", EdgeType.DECIDED_BY)


def test_graph_query_returns_reachable_nodes(tmp_path: Path) -> None:
    _seed(tmp_path)
    result = runner.invoke(
        app, ["graph", "query", "auth", "--depth", "1", "--project", str(tmp_path)]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    ids = {n["id"] for n in payload["nodes"]}
    assert ids == {"f1", "dec1"}


def test_graph_query_unknown_node_errors(tmp_path: Path) -> None:
    _seed(tmp_path)
    result = runner.invoke(app, ["graph", "query", "ghost", "--project", str(tmp_path)])
    assert result.exit_code == 1
    assert "not found" in result.stdout


def test_graph_why_returns_decisions(tmp_path: Path) -> None:
    _seed(tmp_path)
    result = runner.invoke(app, ["graph", "why", "auth", "--project", str(tmp_path)])
    assert result.exit_code == 0
    decisions = json.loads(result.stdout)
    assert [d["id"] for d in decisions] == ["dec1"]
