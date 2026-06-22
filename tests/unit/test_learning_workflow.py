"""P-V1 Learning workflow: human-gated review/approve/reject/commit + provenance.

Principle 2: ForgeOS never promotes or applies a learning autonomously. Every
transition is human-driven (requires an ``actor``), records provenance, and commit
"Becomes a Skill" — creating a ``Skill`` graph node with queryable lineage back to the
originating proposal (AMENDMENT-v1-scope.md ACs).
"""

from __future__ import annotations

import datetime

import pytest

from forgeos.core.graph import GraphStore, NodeType
from forgeos.core.learning import (
    InvalidTransition,
    LearningService,
    ProposalStatus,
    emit_proposal,
)
from forgeos.testing.fakes import InMemoryStorage

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
T1 = datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC)


def _service() -> tuple[LearningService, InMemoryStorage, GraphStore]:
    store = InMemoryStorage()
    graph = GraphStore(store, clock=lambda: T0)
    return LearningService(store, graph, clock=lambda: T1), store, graph


def _proposal(store: InMemoryStorage, **kw):
    return emit_proposal(
        store,
        kind=kw.pop("kind", "skill.candidate"),
        payload=kw.pop("payload", {"name": "retry-with-backoff"}),
        evidence=kw.pop("evidence", ["used in 3 PRs"]),
        clock=lambda: T0,
        **kw,
    )


# -- approve / reject -------------------------------------------------------------
def test_approve_transitions_and_records_provenance() -> None:
    svc, store, _ = _service()
    p = _proposal(store)
    approved = svc.approve(p.id, actor="yuvraj", note="clear reuse value")
    assert approved.status is ProposalStatus.APPROVED
    assert approved.resolved_at == T1
    assert len(approved.provenance) == 1
    entry = approved.provenance[0]
    assert entry.action == "approve"
    assert entry.actor == "yuvraj"
    assert entry.note == "clear reuse value"
    assert entry.from_status is ProposalStatus.PROPOSED
    assert entry.to_status is ProposalStatus.APPROVED


def test_reject_transitions_and_records_provenance() -> None:
    svc, store, _ = _service()
    p = _proposal(store)
    rejected = svc.reject(p.id, actor="yuvraj", note="too narrow")
    assert rejected.status is ProposalStatus.REJECTED
    assert rejected.provenance[-1].action == "reject"


# -- commit "Becomes a Skill" -----------------------------------------------------
def test_commit_requires_approval_first() -> None:
    svc, store, _ = _service()
    p = _proposal(store)
    with pytest.raises(InvalidTransition):
        svc.commit(p.id, actor="yuvraj")  # still PROPOSED


def test_commit_creates_skill_node_with_lineage() -> None:
    svc, store, graph = _service()
    p = _proposal(store)
    svc.approve(p.id, actor="yuvraj")
    committed = svc.commit(p.id, actor="yuvraj", note="ship it")

    assert committed.status is ProposalStatus.COMMITTED
    assert committed.skill_id is not None
    # forward lineage: proposal -> skill
    skill = graph.get_node(committed.skill_id)
    assert skill is not None
    assert skill.type is NodeType.SKILL
    # backward lineage: skill -> proposal (queryable both ways, no new edge type)
    assert skill.props.get("proposal_id") == p.id
    assert skill.props.get("committed_by") == "yuvraj"
    # provenance accumulated across approve + commit
    assert [e.action for e in committed.provenance] == ["approve", "commit"]


def test_committed_skill_appears_in_graph_skill_nodes() -> None:
    svc, store, graph = _service()
    p = _proposal(store, payload={"name": "cache-keys"})
    svc.approve(p.id, actor="yuvraj")
    svc.commit(p.id, actor="yuvraj")
    skills = graph.nodes(NodeType.SKILL)
    assert len(skills) == 1
    assert skills[0].label == "cache-keys"


# -- state-machine guards ---------------------------------------------------------
def test_approve_only_from_proposed() -> None:
    svc, store, _ = _service()
    p = _proposal(store)
    svc.approve(p.id, actor="yuvraj")
    with pytest.raises(InvalidTransition):
        svc.approve(p.id, actor="yuvraj")  # already APPROVED


def test_cannot_reject_after_commit() -> None:
    svc, store, _ = _service()
    p = _proposal(store)
    svc.approve(p.id, actor="yuvraj")
    svc.commit(p.id, actor="yuvraj")
    with pytest.raises(InvalidTransition):
        svc.reject(p.id, actor="yuvraj")  # COMMITTED is terminal


def test_unknown_proposal_raises() -> None:
    svc, _store, _ = _service()
    with pytest.raises(KeyError):
        svc.approve("prop_does_not_exist", actor="yuvraj")


# -- human-gated: no autonomous promotion (Principle 2) ---------------------------
def test_emit_never_auto_promotes() -> None:
    store = InMemoryStorage()
    p = _proposal(store)
    assert p.status is ProposalStatus.PROPOSED
    assert p.provenance == []
    assert p.skill_id is None


def test_transitions_require_an_actor() -> None:
    svc, store, _ = _service()
    p = _proposal(store)
    with pytest.raises(TypeError):
        svc.approve(p.id)  # type: ignore[call-arg]  # actor is mandatory, keyword-only


# -- review (inspect pending) -----------------------------------------------------
def test_review_lists_only_pending_newest_first() -> None:
    store = InMemoryStorage()
    graph = GraphStore(store)
    svc = LearningService(store, graph, clock=lambda: T1)
    a = emit_proposal(store, kind="a", payload={}, clock=lambda: T0)
    b = emit_proposal(store, kind="b", payload={}, clock=lambda: T1)
    svc.reject(a.id, actor="yuvraj")  # resolved -> excluded from pending
    pending = svc.review()
    assert [p.id for p in pending] == [b.id]
