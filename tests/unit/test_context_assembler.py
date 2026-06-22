from __future__ import annotations

import datetime

from forgeos.adapters.tokenizer import LocalEstimator
from forgeos.core.compression import CardGenerator
from forgeos.core.context_assembly import ContextAssembler
from forgeos.core.graph import EdgeType, GraphStore, NodeType
from forgeos.core.token_intel import TokenLedger
from forgeos.testing.fakes import InMemoryStorage

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


def _build_graph() -> tuple[GraphStore, InMemoryStorage]:
    store = InMemoryStorage()
    graph = GraphStore(store, clock=lambda: T0)
    graph.upsert_node(NodeType.MODULE, "m", node_id="m")
    for name in ("f1", "f2"):
        graph.upsert_node(
            NodeType.FILE, f"m/{name}.py",
            props={"language": "python", "size": 400, "hash": name}, node_id=name,
        )
        graph.add_edge("m", name, EdgeType.CONTAINS)
    # Cards make files compressible.
    gen = CardGenerator(store, graph, clock=lambda: T0)
    gen.compress("f1")
    gen.compress("f2")
    return graph, store


def _assembler(graph: GraphStore, store: InMemoryStorage, budget: int, ledger=None):
    return ContextAssembler(graph, LocalEstimator(), store, budget, ledger)


def test_assembly_is_deterministic() -> None:
    graph, store = _build_graph()
    a = _assembler(graph, store, budget=10_000)
    first = a.build("m", depth=2).model_dump()
    second = a.build("m", depth=2).model_dump()
    assert first == second


def test_budget_enforcement_drops_lowest_ranked() -> None:
    graph, store = _build_graph()
    bundle = _assembler(graph, store, budget=3).build("m", depth=2)
    assert bundle.total_tokens <= 3
    assert bundle.dropped  # something didn't fit
    dropped_entries = [m for m in bundle.manifest if not m.included]
    assert all(m.reason == "dropped:budget" for m in dropped_entries)


def test_manifest_records_ranking_and_decisions() -> None:
    graph, store = _build_graph()
    bundle = _assembler(graph, store, budget=10_000).build("m", depth=2)
    # All candidates appear in the manifest with a score and an inclusion decision.
    refs = {m.ref for m in bundle.manifest}
    assert {"m", "f1", "f2"} <= refs
    assert all(m.reason == "included" for m in bundle.manifest)
    assert all(isinstance(m.tier, int) for m in bundle.manifest)


def test_cards_outrank_stubs() -> None:
    graph, store = _build_graph()
    # 'm' has no card (module not compressed) -> stub; files have cards.
    bundle = _assembler(graph, store, budget=10_000).build("m", depth=2)
    kinds = {i.ref: i.kind for i in bundle.items}
    assert kinds["f1"] == "card"
    assert kinds["m"] == "stub"
    # cards (score 3) come before the stub (score 1)
    assert bundle.items[0].kind == "card"


def test_records_savings_to_ledger() -> None:
    graph, store = _build_graph()
    ledger = TokenLedger(store)
    _assembler(graph, store, budget=10_000, ledger=ledger).build("m", depth=2)
    report = ledger.report()
    assert report.events == 1
    # File raw cost (size 400 -> 100 tokens each) >> card purpose cost -> savings.
    assert report.total_raw_equiv > report.compressed_tokens
    assert report.total_saved > 0


def test_unknown_target_yields_empty_bundle() -> None:
    graph, store = _build_graph()
    bundle = _assembler(graph, store, budget=100).build("ghost")
    assert bundle.items == []
    assert bundle.manifest == []
