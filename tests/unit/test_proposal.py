from __future__ import annotations

import datetime

from forgeos.catalog import Collections
from forgeos.core.learning import ProposalStatus, emit_proposal, list_proposals
from forgeos.testing.fakes import InMemoryStorage


def test_emit_proposal_persists_as_proposed() -> None:
    store = InMemoryStorage()
    proposal = emit_proposal(
        store,
        kind="memory.promotion",
        payload={"memory_id": "mem_1"},
        evidence=["accessed 4x"],
        token_savings_est=120,
    )
    assert proposal.status is ProposalStatus.PROPOSED
    assert store.get(Collections.PROPOSALS, proposal.id) is not None


def test_list_proposals_newest_first() -> None:
    store = InMemoryStorage()
    t1 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
    t2 = datetime.datetime(2026, 1, 2, tzinfo=datetime.UTC)
    emit_proposal(store, kind="a", payload={}, clock=lambda: t1)
    emit_proposal(store, kind="b", payload={}, clock=lambda: t2)
    kinds = [p.kind for p in list_proposals(store)]
    assert kinds == ["b", "a"]
