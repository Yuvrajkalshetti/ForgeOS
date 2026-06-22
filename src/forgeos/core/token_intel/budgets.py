"""Token budgets (plan §11.1). ``None`` means unbounded for that scope."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Budgets:
    """Per-scope token budgets."""

    per_request: int | None = 8000
    per_session: int | None = None
    per_project: int | None = None

    def fits(self, used: int, limit: int | None) -> bool:
        """True if ``used`` is within ``limit`` (always true when unbounded)."""
        return limit is None or used <= limit
