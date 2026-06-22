"""Memory CRUD service over a :class:`~forgeos.ports.storage.StoragePort`.

Deterministic and local. De-duplication uses the content hash (exact match within
a scope) — never similarity. A clock is injected for reproducible timestamps.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable

from forgeos.catalog import Collections
from forgeos.core.memory.models import (
    MemoryKind,
    MemoryRecord,
    MemoryScope,
    MemoryStatus,
    Source,
)
from forgeos.ports.storage import StoragePort

Clock = Callable[[], datetime.datetime]


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class MemoryService:
    """Create, read, update, and delete memory records."""

    def __init__(self, store: StoragePort, clock: Clock = _utcnow) -> None:
        self._store = store
        self._clock = clock

    def add(
        self,
        scope: MemoryScope,
        kind: MemoryKind,
        content: str,
        *,
        source: Source | None = None,
        ttl_seconds: int | None = None,
        links: list[str] | None = None,
        dedup: bool = True,
    ) -> MemoryRecord:
        """Store a new record. With ``dedup`` (default), an existing active record
        with identical content in the same scope is returned instead of a duplicate.
        """
        now = self._clock()
        record = MemoryRecord(
            scope=scope,
            kind=kind,
            content=content,
            source=source or Source(),
            created_at=now,
            updated_at=now,
            last_accessed_at=now,
            ttl_seconds=ttl_seconds,
            links=links or [],
        )
        if dedup:
            existing = self._find_duplicate(record)
            if existing is not None:
                return existing
        self._save(record)
        return record

    def get(self, record_id: str) -> MemoryRecord | None:
        row = self._store.get(Collections.MEMORY, record_id)
        return MemoryRecord.model_validate(row) if row is not None else None

    def query(
        self,
        scope: MemoryScope | None = None,
        kind: MemoryKind | None = None,
        status: MemoryStatus | None = None,
    ) -> list[MemoryRecord]:
        """Return matching records, newest first."""
        records = [
            MemoryRecord.model_validate(row)
            for row in self._store.query(Collections.MEMORY)
        ]
        if scope is not None:
            records = [r for r in records if r.scope == scope]
        if kind is not None:
            records = [r for r in records if r.kind == kind]
        if status is not None:
            records = [r for r in records if r.status == status]
        return sorted(records, key=lambda r: r.created_at, reverse=True)

    def touch(self, record_id: str) -> MemoryRecord | None:
        """Record an access: bump count, refresh recency, restore salience."""
        record = self.get(record_id)
        if record is None:
            return None
        record.access_count += 1
        record.last_accessed_at = self._clock()
        record.updated_at = record.last_accessed_at
        record.salience = 1.0  # fresh access resets recency-based salience
        self._save(record)
        return record

    def delete(self, record_id: str) -> None:
        self._store.delete(Collections.MEMORY, record_id)

    def save(self, record: MemoryRecord) -> None:
        """Persist an updated record (used by the lifecycle manager)."""
        self._save(record)

    def _save(self, record: MemoryRecord) -> None:
        self._store.put(Collections.MEMORY, record.id, record.model_dump(mode="json"))

    def _find_duplicate(self, record: MemoryRecord) -> MemoryRecord | None:
        target = record.content_hash()
        for candidate in self.query(scope=record.scope, status=MemoryStatus.ACTIVE):
            if candidate.content_hash() == target:
                return candidate
        return None
