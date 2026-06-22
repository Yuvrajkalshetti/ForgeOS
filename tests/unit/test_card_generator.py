from __future__ import annotations

import datetime

from forgeos.catalog import Collections
from forgeos.core.compression import CardGenerator
from forgeos.core.compression.schema import validate_card
from forgeos.core.graph import EdgeType, GraphStore, NodeType
from forgeos.testing.fakes import InMemoryStorage

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


def _fixture() -> tuple[CardGenerator, GraphStore, InMemoryStorage]:
    store = InMemoryStorage()
    graph = GraphStore(store, clock=lambda: T0)
    graph.upsert_node(NodeType.MODULE, "auth", node_id="auth")
    graph.upsert_node(
        NodeType.FILE, "auth/main.py",
        props={"language": "python", "size": 42, "hash": "H1"}, node_id="f1",
    )
    graph.upsert_node(NodeType.DEPENDENCY, "httpx", node_id="dep:httpx")
    graph.upsert_node(NodeType.DECISION, "use jwt", node_id="dec1")
    graph.add_edge("auth", "f1", EdgeType.CONTAINS)
    graph.add_edge("f1", "dep:httpx", EdgeType.DEPENDS_ON)
    graph.add_edge("f1", "dec1", EdgeType.DECIDED_BY)
    return CardGenerator(store, graph, clock=lambda: T0), graph, store


def test_file_card_is_deterministic_and_provider_free() -> None:
    gen, _, _ = _fixture()
    card = gen.compress("f1")
    assert card.card_id == "card:File:f1"
    assert "python" in card.purpose
    assert card.provider.name == "forgeos"
    assert card.provider.model == "deterministic"
    assert [d.name for d in card.dependencies] == ["httpx"]
    assert card.dependencies[0].kind == "external"
    assert [k.decision_node_id for k in card.key_decisions] == ["dec1"]
    validate_card(card.model_dump(mode="json"))


def test_repeated_compress_is_identical() -> None:
    gen, _, _ = _fixture()
    assert gen.compress("f1") == gen.compress("f1")


def test_card_links_into_graph() -> None:
    gen, graph, store = _fixture()
    gen.compress("f1")
    assert store.get(Collections.CARDS, "card:File:f1") is not None
    assert graph.get_node("card:File:f1") is not None
    summarized = [e for e in graph.edges() if e.type == EdgeType.SUMMARIZED_BY]
    assert summarized[0].src_id == "f1"
    assert summarized[0].dst_id == "card:File:f1"


def test_source_hash_invalidation_regenerates() -> None:
    gen, graph, _ = _fixture()
    first = gen.compress("f1")
    graph.upsert_node(
        NodeType.FILE, "auth/main.py",
        props={"language": "python", "size": 99, "hash": "H2"}, node_id="f1",
    )
    second = gen.compress("f1")
    assert first.source_hash == "H1"
    assert second.source_hash == "H2"


def test_module_card_aggregates_files_and_deps() -> None:
    gen, _, _ = _fixture()
    card = gen.compress("auth")
    assert card.purpose == "Module 'auth' containing 1 file(s)."
    assert [m.name for m in card.modules] == ["auth/main.py"]
    assert [d.name for d in card.dependencies] == ["httpx"]
