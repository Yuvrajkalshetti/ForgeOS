"""Human-gated Learning workflow: review → approve / reject → commit.

ForgeOS never promotes a learning autonomously (Principle 2). Every transition here
requires an explicit human ``actor`` (keyword-only), records provenance, and is
validated against an explicit state machine. ``commit`` performs "Become a Skill":
it creates a :class:`~forgeos.core.graph.NodeType.SKILL` node whose ``props`` carry
queryable lineage back to the originating proposal (no new node/edge type, no schema
change — per ADR 0012 / AMENDMENT-v1-scope.md).
"""

from __future__ import annotations

import datetime
from collections.abc import Callable

from forgeos._ids import new_id
from forgeos._time import utcnow
from forgeos.catalog import Collections
from forgeos.core.graph import GraphStore, Node, NodeType
from forgeos.core.learning.proposal import (
    LearningProposal,
    ProposalStatus,
    ProvenanceEntry,
)
from forgeos.ports.storage import StoragePort

Clock = Callable[[], datetime.datetime]

# Allowed human-driven transitions. Terminal states (REJECTED, COMMITTED) have none.
_TRANSITIONS: dict[str, dict[ProposalStatus, ProposalStatus]] = {
    "approve": {ProposalStatus.PROPOSED: ProposalStatus.APPROVED},
    "reject": {
        ProposalStatus.PROPOSED: ProposalStatus.REJECTED,
        ProposalStatus.APPROVED: ProposalStatus.REJECTED,
    },
    "commit": {ProposalStatus.APPROVED: ProposalStatus.COMMITTED},
}


class InvalidTransition(Exception):
    """Raised when a learning transition is not allowed from the current status."""


class LearningService:
    """Drive proposals through the human-gated review/approve/reject/commit pipeline."""

    def __init__(self, store: StoragePort, graph: GraphStore, clock: Clock = utcnow) -> None:
        self._store = store
        self._graph = graph
        self._clock = clock

    # -- review ----------------------------------------------------------------
    def get(self, proposal_id: str) -> LearningProposal | None:
        row = self._store.get(Collections.PROPOSALS, proposal_id)
        return LearningProposal.model_validate(row) if row is not None else None

    def review(self) -> list[LearningProposal]:
        """Proposals awaiting a human decision (``proposed``), newest first."""
        rows = self._store.query(Collections.PROPOSALS)
        pending = [
            p
            for p in (LearningProposal.model_validate(r) for r in rows)
            if p.status is ProposalStatus.PROPOSED
        ]
        return sorted(pending, key=lambda p: p.created_at, reverse=True)

    # -- transitions (human-only; ``actor`` is mandatory and keyword-only) ------
    def approve(self, proposal_id: str, *, actor: str, note: str = "") -> LearningProposal:
        return self._transition(proposal_id, "approve", actor=actor, note=note)

    def reject(self, proposal_id: str, *, actor: str, note: str = "") -> LearningProposal:
        return self._transition(proposal_id, "reject", actor=actor, note=note)

    def commit(self, proposal_id: str, *, actor: str, note: str = "") -> LearningProposal:
        """Approve → commit. Creates a Skill node with lineage back to the proposal."""
        proposal = self._transition(proposal_id, "commit", actor=actor, note=note, save=False)
        skill = self._become_skill(proposal, actor)
        proposal.skill_id = skill.id
        self._save(proposal)
        return proposal

    # -- internals -------------------------------------------------------------
    def _transition(
        self, proposal_id: str, action: str, *, actor: str, note: str, save: bool = True
    ) -> LearningProposal:
        proposal = self.get(proposal_id)
        if proposal is None:
            raise KeyError(proposal_id)
        target = _TRANSITIONS[action].get(proposal.status)
        if target is None:
            raise InvalidTransition(
                f"cannot {action} a proposal in status {proposal.status.value}"
            )
        now = self._clock()
        proposal.provenance.append(
            ProvenanceEntry(
                action=action,
                actor=actor,
                note=note,
                from_status=proposal.status,
                to_status=target,
                at=now,
            )
        )
        proposal.status = target
        proposal.resolved_at = now
        if save:
            self._save(proposal)
        return proposal

    def _become_skill(self, proposal: LearningProposal, actor: str) -> Node:
        label = str(proposal.payload.get("name") or proposal.payload.get("title") or proposal.kind)
        return self._graph.upsert_node(
            NodeType.SKILL,
            label=label,
            props={
                "proposal_id": proposal.id,
                "kind": proposal.kind,
                "committed_by": actor,
                "committed_at": self._clock().isoformat(),
                "evidence": proposal.evidence,
                "reuse_value": proposal.reuse_value,
            },
            node_id=new_id("skill"),
        )

    def _save(self, proposal: LearningProposal) -> None:
        self._store.put(Collections.PROPOSALS, proposal.id, proposal.model_dump(mode="json"))
