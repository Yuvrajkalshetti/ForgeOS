"""Learning: human-gated proposals and the review/approve/reject/commit pipeline.

Proposals are *observations awaiting human approval*; nothing here promotes or applies
anything autonomously (Principle 2). :func:`emit_proposal` records an observation;
:class:`LearningService` drives the human-only transitions, and ``commit`` performs
"Become a Skill" (creates a Skill graph node with lineage).
"""

from __future__ import annotations

from forgeos.core.learning.proposal import (
    LearningProposal,
    ProposalStatus,
    ProvenanceEntry,
    emit_proposal,
    list_proposals,
)
from forgeos.core.learning.service import InvalidTransition, LearningService

__all__ = [
    "InvalidTransition",
    "LearningProposal",
    "LearningService",
    "ProposalStatus",
    "ProvenanceEntry",
    "emit_proposal",
    "list_proposals",
]
