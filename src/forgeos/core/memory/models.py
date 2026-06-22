"""Memory domain models (plan §4).

Deterministic and local: a record's identity for de-duplication is a SHA-256 over
(scope, kind, content) — no embeddings, no semantic similarity. Salience is a pure
function of recency (see :mod:`.lifecycle`), not a learned score.
"""

from __future__ import annotations

import datetime
import hashlib
from enum import Enum

from pydantic import BaseModel, Field

from forgeos._ids import new_id


def utcnow() -> datetime.datetime:
    """Timezone-aware current UTC time (the default clock)."""
    return datetime.datetime.now(datetime.UTC)


class MemoryScope(str, Enum):
    SESSION = "session"
    PROJECT = "project"
    USER = "user"
    LEARNING = "learning"


class MemoryKind(str, Enum):
    FACT = "fact"
    SUMMARY = "summary"
    PREFERENCE = "preference"
    EVENT = "event"
    OBSERVATION = "observation"


class MemoryStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Source(BaseModel):
    """Provenance for a memory record."""

    type: str = "user"
    ref: str | None = None


class MemoryRecord(BaseModel):
    """A single memory across any scope."""

    id: str = Field(default_factory=lambda: new_id("mem"))
    scope: MemoryScope
    kind: MemoryKind
    content: str
    source: Source = Field(default_factory=Source)
    created_at: datetime.datetime = Field(default_factory=utcnow)
    updated_at: datetime.datetime = Field(default_factory=utcnow)
    last_accessed_at: datetime.datetime = Field(default_factory=utcnow)
    access_count: int = 0
    salience: float = 1.0
    ttl_seconds: int | None = None
    status: MemoryStatus = MemoryStatus.ACTIVE
    links: list[str] = Field(default_factory=list)

    def content_hash(self) -> str:
        """Stable de-duplication key: SHA-256 of scope, kind, and content."""
        digest = hashlib.sha256()
        digest.update(f"{self.scope.value}|{self.kind.value}|{self.content}".encode())
        return digest.hexdigest()
