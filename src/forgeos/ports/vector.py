"""Vector port — defined but unwired in V1.

V1 retrieval is graph-first and deterministic; embeddings are explicitly out of
scope. This seam exists so V2 can add a vector adapter without touching the core.
Any V1 implementation must report ``enabled = False`` and refuse operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VectorMatch:
    """A similarity hit: the stored key and its score."""

    key: str
    score: float


class VectorPort(Protocol):
    """Vector index interface. Disabled in V1 (graph-first retrieval)."""

    enabled: bool

    def upsert(self, key: str, vector: list[float], payload: dict[str, object]) -> None:
        """Store or replace a vector under ``key``."""
        ...

    def search(self, vector: list[float], k: int = 5) -> list[VectorMatch]:
        """Return the ``k`` nearest matches to ``vector``."""
        ...
