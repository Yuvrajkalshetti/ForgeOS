"""SQLite-backed :class:`~forgeos.ports.storage.StoragePort` implementation.

A single generic ``records`` table (see ADR 0008) keyed by ``(collection, id)``
with a JSON ``data`` column. This is the rebuildable query index; the canonical
data lives in YAML snapshots (see :mod:`.snapshots`).
"""

from __future__ import annotations

import datetime
import json
import sqlite3
from pathlib import Path
from typing import Any

from forgeos.adapters.storage.sqlite.migrations import run_migrations
from forgeos.ports.storage import Record


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


class SqliteStorage:
    """Generic record store over SQLite. Single-writer."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @classmethod
    def open(cls, path: Path | str = ":memory:") -> SqliteStorage:
        """Open (or create) a database at ``path`` and run migrations."""
        conn = sqlite3.connect(str(path))
        run_migrations(conn)
        return cls(conn)

    def put(self, collection: str, record_id: str, data: Record) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO records (collection, id, data, updated_at) "
            "VALUES (?, ?, ?, ?)",
            (collection, record_id, json.dumps(data, default=str), _now()),
        )
        self._conn.commit()

    def get(self, collection: str, record_id: str) -> Record | None:
        row = self._conn.execute(
            "SELECT data FROM records WHERE collection = ? AND id = ?",
            (collection, record_id),
        ).fetchone()
        if row is None:
            return None
        result: Record = json.loads(row[0])
        return result

    def delete(self, collection: str, record_id: str) -> None:
        self._conn.execute(
            "DELETE FROM records WHERE collection = ? AND id = ?",
            (collection, record_id),
        )
        self._conn.commit()

    def query(self, collection: str, where: Record | None = None) -> list[Record]:
        rows = self._conn.execute(
            "SELECT data FROM records WHERE collection = ? ORDER BY id",
            (collection,),
        ).fetchall()
        records: list[Record] = [json.loads(row[0]) for row in rows]
        if not where:
            return records
        return [r for r in records if all(r.get(k) == v for k, v in where.items())]

    def collections(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT collection FROM records ORDER BY collection"
        ).fetchall()
        return [row[0] for row in rows]

    def clear(self) -> None:
        """Remove all records (used when rebuilding the index from snapshots)."""
        self._conn.execute("DELETE FROM records")
        self._conn.commit()

    def raw_items(self, collection: str) -> list[tuple[str, dict[str, Any]]]:
        """Return ``(id, data)`` pairs for a collection (for snapshot writing)."""
        rows = self._conn.execute(
            "SELECT id, data FROM records WHERE collection = ? ORDER BY id",
            (collection,),
        ).fetchall()
        return [(row[0], json.loads(row[1])) for row in rows]

    def close(self) -> None:
        self._conn.close()
