"""Advisory artifact models.

Mirror the required Mentor and Auditor output structures. Artifacts are persisted as
graph nodes (``MentorRecommendation`` / ``AuditFinding``); ``AdvisorySession`` groups
a lineage and is persisted as a record. Models are advisory-only — they carry no
capability to execute or approve.
"""

from __future__ import annotations

import datetime

from pydantic import BaseModel, Field

from forgeos._ids import new_id

_LEAD = {
    "proposal": "Your proposal:",
    "question": "Your question:",
    "request": "Your request:",
}


def _utcnow_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


class AdvisorProvider(BaseModel):
    """Provenance for an advisory artifact."""

    name: str
    model: str


def _section(title: str, body: str) -> str:
    return f"## {title}\n{body}\n"


def _bullets(items: list[str]) -> str:
    return "\n".join(f"- {i}" for i in items) if items else "- (none)"


class MentorRecommendation(BaseModel):
    """Mentor's structured pre-execution guidance."""

    id: str = Field(default_factory=lambda: new_id("mrec"))
    kind: str = "proposal"  # proposal | question | request
    request: str
    understanding: str = ""
    assumptions: list[str] = Field(default_factory=list)
    challenges: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    recommendation: str = ""
    proposed_plan: list[str] = Field(default_factory=list)
    confidence: str = ""
    grounding_refs: list[str] = Field(default_factory=list)  # context items used (P6.6)
    provider: AdvisorProvider
    created_at: str = Field(default_factory=_utcnow_iso)

    @property
    def lead(self) -> str:
        return _LEAD.get(self.kind, _LEAD["request"])

    def to_markdown(self) -> str:
        return (
            f"{self.lead} {self.request}\n\n"
            + _section("Understanding", self.understanding)
            + _section("Assumptions", _bullets(self.assumptions))
            + _section("Challenges", _bullets(self.challenges))
            + _section("Gaps", _bullets(self.gaps))
            + _section("Alternatives", _bullets(self.alternatives))
            + _section("Recommendation", self.recommendation)
            + _section("Proposed Plan", _bullets(self.proposed_plan))
            + _section("Confidence", self.confidence)
        )


class AuditFinding(BaseModel):
    """Auditor's structured, evidence-based assessment."""

    id: str = Field(default_factory=lambda: new_id("afind"))
    scope: str
    evidence_review: str = ""
    architecture_compliance: str = ""
    test_coverage: str = ""
    risks: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    recommendation: str = ""
    confidence: str = ""
    grounding_refs: list[str] = Field(default_factory=list)  # context items used (P6.6)
    provider: AdvisorProvider
    created_at: str = Field(default_factory=_utcnow_iso)

    def to_markdown(self) -> str:
        return (
            _section("Scope", self.scope)
            + _section("Evidence Review", self.evidence_review)
            + _section("Architecture Compliance", self.architecture_compliance)
            + _section("Test Coverage", self.test_coverage)
            + _section("Risks", _bullets(self.risks))
            + _section("Violations", _bullets(self.violations))
            + _section("Recommendation", self.recommendation)
            + _section("Confidence", self.confidence)
        )


class AdvisorySession(BaseModel):
    """Groups a lineage: request → recommendation → decision → implementation → finding."""

    id: str = Field(default_factory=lambda: new_id("asess"))
    request: str
    recommendation_id: str | None = None
    decision_id: str | None = None
    implementation_refs: list[str] = Field(default_factory=list)
    finding_id: str | None = None
    created_at: str = Field(default_factory=_utcnow_iso)
    updated_at: str = Field(default_factory=_utcnow_iso)
