"""Learning proposals.

A proposal is an *observation awaiting human approval*. ForgeOS never promotes or
applies one autonomously (Principle 2). P2 lifecycle emits proposals for memory
promotion and consolidation; the human-gated review/approve/reject/commit pipeline
lives in :mod:`forgeos.core.learning.service`.

Every proposal carries the fields the architecture requires: evidence, benefits,
risks, expected reuse value, and a token-savings estimate. Each human decision is
appended to ``provenance`` (no decision is ever applied autonomously).
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from forgeos._ids import new_id
from forgeos.catalog import Collections
from forgeos.ports.storage import StoragePort

Clock = Callable[[], datetime.datetime]


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class ProposalStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMMITTED = "committed"  # approved -> committed ("Become a Skill")


class ProvenanceEntry(BaseModel):
    """One human decision in a proposal's lifecycle. Append-only audit record."""

    action: str  # approve | reject | commit
    actor: str
    note: str = ""
    from_status: ProposalStatus
    to_status: ProposalStatus
    at: datetime.datetime = Field(default_factory=_utcnow)


class LearningProposal(BaseModel):
    """A human-reviewable proposal. Defaults to ``proposed`` and is never applied."""

    id: str = Field(default_factory=lambda: new_id("prop"))
    kind: str
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    benefits: str = ""
    risks: str = ""
    reuse_value: str = ""
    token_savings_est: int = 0
    status: ProposalStatus = ProposalStatus.PROPOSED
    provenance: list[ProvenanceEntry] = Field(default_factory=list)
    skill_id: str | None = None  # set when commit "Becomes a Skill"
    created_at: datetime.datetime = Field(default_factory=_utcnow)
    resolved_at: datetime.datetime | None = None


def emit_proposal(
    store: StoragePort,
    kind: str,
    payload: dict[str, Any],
    *,
    evidence: list[str] | None = None,
    benefits: str = "",
    risks: str = "",
    reuse_value: str = "",
    token_savings_est: int = 0,
    clock: Clock = _utcnow,
) -> LearningProposal:
    """Persist a new ``proposed`` proposal and return it. Never auto-applies."""
    proposal = LearningProposal(
        kind=kind,
        payload=payload,
        evidence=evidence or [],
        benefits=benefits,
        risks=risks,
        reuse_value=reuse_value,
        token_savings_est=token_savings_est,
        created_at=clock(),
    )
    store.put(Collections.PROPOSALS, proposal.id, proposal.model_dump(mode="json"))
    return proposal


def list_proposals(store: StoragePort) -> list[LearningProposal]:
    """Return all proposals, newest first."""
    rows = store.query(Collections.PROPOSALS)
    proposals = [LearningProposal.model_validate(row) for row in rows]
    return sorted(proposals, key=lambda p: p.created_at, reverse=True)
