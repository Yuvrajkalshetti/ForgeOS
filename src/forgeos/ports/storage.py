"""Storage port.

A minimal collection/record interface. The SQLite adapter (P1) implements this
as the rebuildable query index, with YAML/JSON snapshots as the source of truth.
Records are plain mappings here; typed domain models (Node, Edge, MemoryRecord)
are layered on top by the core engines without changing this seam.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

Record = dict[str, Any]


@runtime_checkable
class StoragePort(Protocol):
    """Key/collection record store. Implementations must be single-writer safe."""

    def put(self, collection: str, record_id: str, data: Record) -> None:
        """Insert or replace ``data`` under ``record_id`` in ``collection``."""
        ...

    def get(self, collection: str, record_id: str) -> Record | None:
        """Return the record, or ``None`` if absent."""
        ...

    def delete(self, collection: str, record_id: str) -> None:
        """Remove ``record_id`` if present; a no-op otherwise."""
        ...

    def query(self, collection: str, where: Record | None = None) -> list[Record]:
        """Return records in ``collection`` matching every key/value in ``where``."""
        ...

    def collections(self) -> list[str]:
        """Return the names of all known collections."""
        ...
