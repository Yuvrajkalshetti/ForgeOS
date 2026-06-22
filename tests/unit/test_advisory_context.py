from __future__ import annotations

import ast
import datetime
from pathlib import Path

from forgeos.adapters.tokenizer import LocalEstimator
from forgeos.catalog import Collections
from forgeos.core.advisory import AdvisoryContextBuilder
from forgeos.core.compression import CardGenerator
from forgeos.core.context_assembly.models import tier_for
from forgeos.core.graph import EdgeType, GraphStore, NodeType
from forgeos.core.memory import MemoryKind, MemoryScope, MemoryService
from forgeos.core.token_intel import TokenLedger
from forgeos.testing.fakes import InMemoryStorage

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


def _fixture(*, make_card: bool = True):
    store = InMemoryStorage()
    graph = GraphStore(store, clock=lambda: T0)
    memory = MemoryService(store, clock=lambda: T0)
    graph.upsert_node(NodeType.MODULE, "auth", node_id="auth")
    graph.upsert_node(
        NodeType.FILE, "auth/main.py",
        props={"language": "python", "size": 400, "hash": "H1"}, node_id="f1",
    )
    graph.add_edge("auth", "f1", EdgeType.CONTAINS)
    graph.upsert_node(NodeType.DECISION, "use jwt", node_id="dec1")
    graph.add_edge("f1", "dec1", EdgeType.DECIDED_BY)  # reachable decision
    graph.upsert_node(NodeType.DECISION, "rotate keys", node_id="dec2")  # recent, unreachable
    graph.upsert_node(
        NodeType.AUDIT_FINDING, "prior audit",
        props={"recommendation": "fix logging", "violations": ["v1"]}, node_id="af1",
    )
    store.put(Collections.REPO_PROFILE, "profile",
              {"root": "repo", "languages": ["python"], "file_count": 1, "module_count": 1, "hotspots": []})
    if make_card:
        CardGenerator(store, graph, clock=lambda: T0).compress("f1")
    builder = AdvisoryContextBuilder(graph, store, memory, LocalEstimator(), TokenLedger(store))
    return builder, graph, store, memory


def test_mentor_grounding_includes_existing_knowledge() -> None:
    builder, *_ = _fixture()
    bundle = builder.for_mentor("auth", budget=10_000, depth=3)
    kinds = {i.kind for i in bundle.items}
    assert "card" in kinds  # f1 card (cards-first)
    assert "decision" in kinds
    assert "finding" in kinds
    assert "repo_profile" in kinds
    # card tier 0 sorts first
    assert bundle.items[0].kind == "card"


def test_mentor_grounding_is_deterministic() -> None:
    builder1, *_ = _fixture()
    builder2, *_ = _fixture()
    assert builder1.for_mentor("auth", budget=10_000, depth=3).model_dump() == (
        builder2.for_mentor("auth", budget=10_000, depth=3).model_dump()
    )


def test_ac11_valid_card_beats_source_and_memory() -> None:
    builder, *_ = _fixture(make_card=True)
    bundle = builder.for_mentor("auth", budget=10_000, depth=3, allow_source=True, source_root=Path("/x"))
    f1 = [i for i in bundle.items if i.ref == "f1"][0]
    assert f1.kind == "card"  # valid card wins over source


def test_ac11_stale_card_escalates_to_memory_then_source() -> None:
    builder, graph, store, memory = _fixture(make_card=True)
    # Make the card stale: file hash changes after the card was generated.
    graph.upsert_node(NodeType.FILE, "auth/main.py",
                      props={"language": "python", "size": 400, "hash": "H2"}, node_id="f1")
    memory.add(MemoryScope.PROJECT, MemoryKind.FACT, "auth uses JWT", links=["f1"])
    bundle = builder.for_mentor("auth", budget=10_000, depth=3)
    f1 = [i for i in bundle.items if i.ref == "f1"][0]
    assert f1.kind == "memory"  # stale card -> escalate to memory (not source)


def test_ac11_no_card_no_memory_uses_source_only_when_allowed() -> None:
    builder, *_ = _fixture(make_card=False)
    # No card, no subject memory: without allow_source -> stub; with -> source.
    stub_bundle = builder.for_mentor("auth", budget=10_000, depth=3, allow_source=False)
    assert [i for i in stub_bundle.items if i.ref == "f1"][0].kind == "stub"

    builder2, *_ = _fixture(make_card=False)
    src_bundle = builder2.for_mentor("auth", budget=10_000, depth=3, allow_source=True, source_root=Path("/missing"))
    assert [i for i in src_bundle.items if i.ref == "f1"][0].kind == "source"


def test_decisions_reachable_first_then_recent() -> None:
    builder, *_ = _fixture()
    bundle = builder.for_mentor("auth", budget=10_000, depth=3)
    decisions = [i.ref for i in bundle.items if i.kind == "decision"]
    assert decisions.index("dec1") < decisions.index("dec2")  # reachable before recent-N


def test_budget_enforced_and_savings_recorded() -> None:
    builder, _g, store, _m = _fixture()
    bundle = builder.for_mentor("auth", budget=3, depth=3)
    assert bundle.total_tokens <= 3
    assert bundle.dropped
    report = TokenLedger(store).report()
    assert report.events >= 1
    assert report.total_raw_equiv >= report.compressed_tokens


def test_auditor_grounding_includes_criteria_and_evidence() -> None:
    builder, *_ = _fixture()
    bundle = builder.for_auditor(
        "auth", budget=10_000, criteria="all tests pass", evidence="ci green", depth=3
    )
    kinds = [i.kind for i in bundle.items]
    assert "criteria" in kinds and "evidence" in kinds and "decision" in kinds
    # criteria (tier 1) outranks evidence (tier 5)
    assert tier_for("criteria") < tier_for("evidence")
    crit_pos = next(n for n, i in enumerate(bundle.items) if i.kind == "criteria")
    ev_pos = next(n for n, i in enumerate(bundle.items) if i.kind == "evidence")
    assert crit_pos < ev_pos


def test_free_text_focus_without_node_is_graceful() -> None:
    builder, *_ = _fixture()
    bundle = builder.for_mentor("some vague idea with no node", budget=10_000)
    assert bundle.target == "some vague idea with no node"
    # still grounded by recent decisions/findings/profile even with no focus node
    assert any(i.kind in {"decision", "finding", "repo_profile"} for i in bundle.items)


def test_context_builder_is_provider_free() -> None:
    src = Path(__file__).resolve().parents[2] / "src" / "forgeos" / "core" / "advisory" / "context.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert "forgeos.ports.provider" not in imports
    assert not any(m.startswith("forgeos.adapters") for m in imports)
