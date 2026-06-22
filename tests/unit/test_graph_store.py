from __future__ import annotations

import datetime

import pytest

from forgeos.core.graph import EdgeType, GraphStore, NodeType
from forgeos.core.graph.store import Direction
from forgeos.testing.fakes import InMemoryStorage

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


def _graph() -> GraphStore:
    return GraphStore(InMemoryStorage(), clock=lambda: T0)


def test_upsert_node_creates_then_updates() -> None:
    graph = _graph()
    node = graph.upsert_node(NodeType.MODULE, "app", node_id="node_app")
    assert node.id == "node_app"
    updated = graph.upsert_node(NodeType.MODULE, "app-renamed", node_id="node_app")
    assert updated.label == "app-renamed"
    assert graph.get_node("node_app") is not None
    assert len(graph.nodes()) == 1  # upsert, not duplicate


def test_add_edge_requires_existing_endpoints() -> None:
    graph = _graph()
    graph.upsert_node(NodeType.MODULE, "m", node_id="m")
    with pytest.raises(ValueError, match="must exist"):
        graph.add_edge("m", "missing", EdgeType.CONTAINS)


def test_add_edge_validates_types() -> None:
    graph = _graph()
    graph.upsert_node(NodeType.FILE, "a.py", node_id="f1")
    graph.upsert_node(NodeType.FILE, "b.py", node_id="f2")
    with pytest.raises(ValueError, match="not allowed"):
        graph.add_edge("f1", "f2", EdgeType.CONTAINS)  # File->File invalid


def test_add_edge_is_idempotent() -> None:
    graph = _graph()
    graph.upsert_node(NodeType.MODULE, "m", node_id="m")
    graph.upsert_node(NodeType.FILE, "a.py", node_id="f")
    e1 = graph.add_edge("m", "f", EdgeType.CONTAINS)
    e2 = graph.add_edge("m", "f", EdgeType.CONTAINS)
    assert e1.id == e2.id
    assert len(graph.edges()) == 1


def test_neighbors_direction() -> None:
    graph = _graph()
    graph.upsert_node(NodeType.MODULE, "m", node_id="m")
    graph.upsert_node(NodeType.FILE, "f", node_id="f")
    graph.add_edge("m", "f", EdgeType.CONTAINS)
    assert [n.id for _e, n in graph.neighbors("m", direction=Direction.OUT)] == ["f"]
    assert [n.id for _e, n in graph.neighbors("f", direction=Direction.IN)] == ["m"]
    assert graph.neighbors("f", direction=Direction.OUT) == []


def test_traverse_bounded_and_deterministic() -> None:
    graph = _graph()
    graph.upsert_node(NodeType.MODULE, "m", node_id="m")
    for name in ("c", "b", "a"):
        graph.upsert_node(NodeType.FILE, name, node_id=name)
        graph.add_edge("m", name, EdgeType.CONTAINS)
    reachable = [n.id for n in graph.traverse("m", max_depth=1)]
    assert reachable == ["a", "b", "c"]  # sorted, deterministic


def test_traverse_respects_depth_limit() -> None:
    graph = _graph()
    # chain: m -> dep1 (depends_on); dep1 has no further out-edges
    graph.upsert_node(NodeType.MODULE, "m", node_id="m")
    graph.upsert_node(NodeType.DEPENDENCY, "dep1", node_id="d1")
    graph.add_edge("m", "d1", EdgeType.DEPENDS_ON)
    assert [n.id for n in graph.traverse("m", max_depth=1)] == ["d1"]
    assert graph.traverse("d1", max_depth=5) == []


def test_traverse_filters_by_node_type() -> None:
    graph = _graph()
    graph.upsert_node(NodeType.MODULE, "m", node_id="m")
    graph.upsert_node(NodeType.FILE, "f", node_id="f")
    graph.upsert_node(NodeType.DEPENDENCY, "d", node_id="d")
    graph.add_edge("m", "f", EdgeType.CONTAINS)
    graph.add_edge("m", "d", EdgeType.DEPENDS_ON)
    files = graph.traverse("m", max_depth=1, node_types=[NodeType.FILE])
    assert [n.id for n in files] == ["f"]


def test_why_combines_decided_by_and_affects() -> None:
    graph = _graph()
    graph.upsert_node(NodeType.MODULE, "auth", node_id="auth")
    graph.upsert_node(NodeType.DECISION, "use jwt", node_id="dec1")
    graph.upsert_node(NodeType.DECISION, "rotate keys", node_id="dec2")
    graph.add_edge("auth", "dec1", EdgeType.DECIDED_BY)  # outgoing
    graph.add_edge("dec2", "auth", EdgeType.AFFECTS)  # incoming
    decisions = graph.why("auth")
    assert [n.id for n in decisions] == ["dec1", "dec2"]


def test_why_accepts_label_and_returns_empty_for_unknown() -> None:
    graph = _graph()
    graph.upsert_node(NodeType.MODULE, "billing", node_id="b")
    graph.upsert_node(NodeType.DECISION, "decimal money", node_id="dec")
    graph.add_edge("b", "dec", EdgeType.DECIDED_BY)
    assert [n.id for n in graph.why("billing")] == ["dec"]  # by label
    assert graph.why("nonexistent") == []
