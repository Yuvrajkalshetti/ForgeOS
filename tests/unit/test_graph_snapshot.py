from __future__ import annotations

from pathlib import Path

import yaml

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.core.graph import EdgeType, GraphStore, NodeType


def test_graph_writes_nodes_and_edges_snapshots(tmp_path: Path) -> None:
    snap = tmp_path / "snap"
    graph = GraphStore(SnapshotStore.open(snap))
    graph.upsert_node(NodeType.MODULE, "m", node_id="m")
    graph.upsert_node(NodeType.FILE, "f", node_id="f")
    graph.add_edge("m", "f", EdgeType.CONTAINS)

    nodes_yaml = yaml.safe_load((snap / "nodes.yaml").read_text())
    edges_yaml = yaml.safe_load((snap / "edges.yaml").read_text())
    assert set(nodes_yaml) == {"m", "f"}
    assert len(edges_yaml) == 1


def test_graph_rebuilds_from_snapshots(tmp_path: Path) -> None:
    snap = tmp_path / "snap"
    graph = GraphStore(SnapshotStore.open(snap))
    graph.upsert_node(NodeType.MODULE, "m", node_id="m")
    graph.upsert_node(NodeType.FILE, "f", node_id="f")
    graph.add_edge("m", "f", EdgeType.CONTAINS)

    # Fresh in-memory index over the same snapshots must recover the graph.
    reopened = GraphStore(SnapshotStore.open(snap))
    assert reopened.get_node("m") is not None
    assert [n.id for n in reopened.traverse("m", max_depth=1)] == ["f"]
