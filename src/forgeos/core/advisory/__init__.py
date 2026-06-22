"""Advisory System — Mentor and Auditor (ADR 0010).

A first-class subsystem, **separate from Execution** (``core/orchestrator``). Mentor
and Auditor reason and advise; they never execute, deploy, merge, approve, mutate
execution/learning state, or override human decisions. Final authority is human.

This package must not import ``forgeos.core.orchestrator`` or ``forgeos.core.learning``
(enforced by boundary tests).
"""

from __future__ import annotations

from forgeos.core.advisory.auditor import Auditor
from forgeos.core.advisory.context import AdvisoryContextBuilder
from forgeos.core.advisory.mentor import Mentor
from forgeos.core.advisory.models import AdvisorySession, AuditFinding, MentorRecommendation
from forgeos.core.advisory.session import AdvisorySessionStore

__all__ = [
    "AdvisoryContextBuilder",
    "AdvisorySession",
    "AdvisorySessionStore",
    "AuditFinding",
    "Auditor",
    "Mentor",
    "MentorRecommendation",
]
