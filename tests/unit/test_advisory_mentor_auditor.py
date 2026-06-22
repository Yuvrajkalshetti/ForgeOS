from __future__ import annotations

import asyncio
import datetime

from forgeos.catalog import Collections
from forgeos.core.advisory import Auditor, Mentor
from forgeos.core.graph import EdgeType, GraphStore, NodeType
from forgeos.ports.provider import ProviderRequest, ProviderResult, Usage
from forgeos.testing.fakes import InMemoryStorage

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)

_MENTOR_JSON = (
    '{"kind":"proposal","understanding":"build X","assumptions":["a1"],'
    '"challenges":["c1"],"gaps":["g1"],"alternatives":["alt1","alt2"],'
    '"recommendation":"do the simple thing","proposed_plan":["s1","s2"],'
    '"confidence":"high: clear scope"}'
)
_AUDIT_JSON = (
    '{"evidence_review":"tests provided","architecture_compliance":"compliant",'
    '"test_coverage":"adequate","risks":["r1"],"violations":[],'
    '"recommendation":"accept","confidence":"medium"}'
)


class _JsonProvider:
    name = "fake"

    def __init__(self, reply: str) -> None:
        self._reply = reply

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(text=self._reply, model=request.model, usage=Usage(2, 3), latency_ms=0.0)


def _graph() -> tuple[GraphStore, InMemoryStorage]:
    store = InMemoryStorage()
    return GraphStore(store, clock=lambda: T0), store


def test_mentor_produces_structured_recommendation_and_node() -> None:
    graph, store = _graph()
    mentor = Mentor(_JsonProvider(_MENTOR_JSON), graph, clock=lambda: T0)
    rec = asyncio.run(mentor.advise("add caching", model="m"))

    assert rec.lead == "Your proposal:"
    assert rec.understanding == "build X"
    assert rec.alternatives == ["alt1", "alt2"]
    assert rec.proposed_plan == ["s1", "s2"]
    assert rec.provider.name == "fake"
    # persisted as a graph node
    node = graph.get_node(rec.id)
    assert node is not None and node.type == NodeType.MENTOR_RECOMMENDATION
    # markdown begins with the required lead
    assert rec.to_markdown().startswith("Your proposal:")


def test_mentor_links_advises_and_informs_edges() -> None:
    graph, _ = _graph()
    graph.upsert_node(NodeType.MODULE, "auth", node_id="auth")
    graph.upsert_node(NodeType.DECISION, "use jwt", node_id="dec1")
    mentor = Mentor(_JsonProvider(_MENTOR_JSON), graph, clock=lambda: T0)
    rec = asyncio.run(mentor.advise("review auth", model="m", targets=["auth", "dec1"]))

    edges = {(e.src_id, e.dst_id): e.type for e in graph.edges() if e.src_id == rec.id}
    assert edges[(rec.id, "auth")] == EdgeType.ADVISES
    assert edges[(rec.id, "dec1")] == EdgeType.INFORMS  # Decision -> informs


def test_auditor_produces_finding_and_node_and_audits_edge() -> None:
    graph, _ = _graph()
    graph.upsert_node(NodeType.MODULE, "auth", node_id="auth")
    auditor = Auditor(_JsonProvider(_AUDIT_JSON), graph, clock=lambda: T0)
    finding = asyncio.run(auditor.audit("auth module", model="m", targets=["auth"]))

    assert finding.architecture_compliance == "compliant"
    assert finding.violations == []
    assert finding.to_markdown().startswith("## Scope")
    node = graph.get_node(finding.id)
    assert node is not None and node.type == NodeType.AUDIT_FINDING
    audits = [e for e in graph.edges() if e.type == EdgeType.AUDITS]
    assert audits[0].src_id == finding.id and audits[0].dst_id == "auth"


def test_advisory_does_not_write_proposals_or_decisions() -> None:
    graph, store = _graph()
    asyncio.run(Mentor(_JsonProvider(_MENTOR_JSON), graph, clock=lambda: T0).advise("x", model="m"))
    asyncio.run(Auditor(_JsonProvider(_AUDIT_JSON), graph, clock=lambda: T0).audit("y", model="m"))
    # No learning state mutated; no human Decision fabricated by advisory.
    assert store.query(Collections.PROPOSALS) == []
    assert graph.nodes(NodeType.DECISION) == []
