"""Canonical names and the knowledge schema version.

Logical record collections (Implementation Plan §5) are addressed by these
constants so engines and adapters never hard-code strings. The physical SQLite
shape for each collection may evolve via migrations; these names and the snapshot
format are the stable contract.
"""

from __future__ import annotations

from typing import Final

# Bumped only when the on-disk snapshot/knowledge format changes incompatibly.
SCHEMA_VERSION: Final[int] = 1


class Collections:
    """Canonical logical collection names."""

    NODES: Final[str] = "nodes"
    EDGES: Final[str] = "edges"
    MEMORY: Final[str] = "memory"
    CARDS: Final[str] = "cards"
    TOKEN_EVENTS: Final[str] = "token_events"
    PROVIDER_STATS: Final[str] = "provider_stats"
    PROPOSALS: Final[str] = "proposals"
    REPO_INDEX: Final[str] = "repo_index"
    REPO_PROFILE: Final[str] = "repo_profile"
    ADVISORY_SESSIONS: Final[str] = "advisory_sessions"


ALL_COLLECTIONS: Final[tuple[str, ...]] = (
    Collections.NODES,
    Collections.EDGES,
    Collections.MEMORY,
    Collections.CARDS,
    Collections.TOKEN_EVENTS,
    Collections.PROVIDER_STATS,
    Collections.PROPOSALS,
    Collections.REPO_INDEX,
    Collections.REPO_PROFILE,
    Collections.ADVISORY_SESSIONS,
)
