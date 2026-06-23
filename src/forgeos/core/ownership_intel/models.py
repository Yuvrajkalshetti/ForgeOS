"""Ownership Intelligence models (V2, E4 — ADR 0016).

Declared ownership comes from human-authored rules; observed ownership is computed
deterministically from the call graph. Criticality / runtime impact remain rule-only
governance metadata — never inferred from code.
"""

from __future__ import annotations

from dataclasses import dataclass, field

UNKNOWN = "Unknown"
UNCLASSIFIED = "Unclassified"


@dataclass(frozen=True)
class OwnershipRule:
    """One ownership rule: a single match predicate + the axes it assigns."""

    match_kind: str  # "symbol" | "name" | "path"
    pattern: str
    domain: str | None = None
    layer: str | None = None
    criticality: str | None = None
    impact: str | None = None


@dataclass
class OwnershipResult:
    """Declared + observed ownership for one symbol."""

    symbol: str
    declared_owner: str = UNKNOWN
    observed_owner: str = UNKNOWN
    agreement: bool = False
    confidence: float = 0.0
    matched_by: str = "default"
    layer: str = UNKNOWN
    criticality: str = UNCLASSIFIED
    impact: str = UNCLASSIFIED
    declared_confidence: float = 0.0
    observed_confidence: float = 0.0
    caller_domains: dict[str, int] = field(default_factory=dict)
