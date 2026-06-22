"""Context assembly models (plan §10.3).

Ranking is by **deterministic priority tiers** (lower tier = higher priority), not
float weights. Within a tier, items keep their gather order (so graph-reachable items
precede recent-N fill). This makes assembly reproducible and explainable.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, Field

# Deterministic priority tiers by item kind (lower = included first under budget).
# Honors AC11: card (0) before memory (7) before source (8).
TIER: Final[dict[str, int]] = {
    "card": 0,
    "criteria": 1,
    "decision": 2,
    "finding": 3,
    "adr": 4,
    "evidence": 5,
    "repo_profile": 6,
    "memory": 7,
    "source": 8,
    "stub": 9,
}
_DEFAULT_TIER: Final[int] = 9


def tier_for(kind: str) -> int:
    """Return the deterministic priority tier for an item kind."""
    return TIER.get(kind, _DEFAULT_TIER)


class ContextItem(BaseModel):
    """A single candidate piece of context.

    ``tokens`` is the assembled (compressed) cost; ``raw_tokens`` is what including
    the uncompressed source would have cost — their gap is the per-item saving.
    ``tier`` is the priority tier; ``order`` is the gather sequence (tie-break).
    """

    ref: str
    kind: str  # card|criteria|decision|finding|adr|evidence|repo_profile|memory|source|stub
    content: str
    tokens: int
    raw_tokens: int
    tier: int
    order: int = 0


class ManifestEntry(BaseModel):
    """Auditable record of an item's tier and inclusion decision."""

    ref: str
    kind: str
    tokens: int
    tier: int
    included: bool
    reason: str


class ContextBundle(BaseModel):
    """The assembled context plus an auditable manifest."""

    target: str
    items: list[ContextItem] = Field(default_factory=list)
    manifest: list[ManifestEntry] = Field(default_factory=list)
    total_tokens: int = 0
    dropped: list[str] = Field(default_factory=list)

    def render(self) -> str:
        """Render included items as grounding text for a provider prompt."""
        if not self.items:
            return ""
        lines = ["## Grounding (ForgeOS knowledge)"]
        for item in self.items:
            lines.append(f"- [{item.kind}] {item.content}")
        return "\n".join(lines)
