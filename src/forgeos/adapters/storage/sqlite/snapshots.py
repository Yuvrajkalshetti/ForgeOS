"""Write-through snapshot store.

Wraps :class:`SqliteStorage` and a snapshot directory. Mutations update SQLite and
then rewrite the affected collection's YAML file — and **YAML is the source of
truth**. ``rebuild_index`` discards SQLite and reloads it from the snapshots, so on
any divergence the snapshot wins (Storage Strategy, plan §21).

Layout: one file per collection, ``<snapshot_dir>/<collection>.yaml``, mapping
record id -> record data, key-sorted for stable git diffs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from forgeos.adapters.storage.sqlite.store import SqliteStorage
from forgeos.ports.storage import Record


def _snapshot_file(snapshot_dir: Path, collection: str) -> Path:
    return snapshot_dir / f"{collection}.yaml"


def load_snapshots(snapshot_dir: Path) -> dict[str, dict[str, Record]]:
    """Load every ``*.yaml`` collection file into ``{collection: {id: data}}``."""
    result: dict[str, dict[str, Record]] = {}
    if not snapshot_dir.is_dir():
        return result
    for path in sorted(snapshot_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            result[path.stem] = {str(k): v for k, v in data.items()}
    return result


class SnapshotStore:
    """A :class:`~forgeos.ports.storage.StoragePort` with YAML write-through."""

    def __init__(self, sqlite: SqliteStorage, snapshot_dir: Path) -> None:
        self._sqlite = sqlite
        self._dir = snapshot_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def open(cls, snapshot_dir: Path, db_path: Path | str = ":memory:") -> SnapshotStore:
        """Open a store, rebuilding the SQLite index from snapshots if present."""
        store = cls(SqliteStorage.open(db_path), snapshot_dir)
        if any(snapshot_dir.glob("*.yaml")):
            store.rebuild_index()
        return store

    def put(self, collection: str, record_id: str, data: Record) -> None:
        self._sqlite.put(collection, record_id, data)
        self._flush_collection(collection)

    def get(self, collection: str, record_id: str) -> Record | None:
        return self._sqlite.get(collection, record_id)

    def delete(self, collection: str, record_id: str) -> None:
        self._sqlite.delete(collection, record_id)
        self._flush_collection(collection)

    def query(self, collection: str, where: Record | None = None) -> list[Record]:
        return self._sqlite.query(collection, where)

    def collections(self) -> list[str]:
        return self._sqlite.collections()

    def rebuild_index(self) -> None:
        """Discard SQLite contents and reload from snapshots (snapshot wins)."""
        self._sqlite.clear()
        for collection, items in load_snapshots(self._dir).items():
            for record_id, data in items.items():
                self._sqlite.put(collection, record_id, data)

    def _flush_collection(self, collection: str) -> None:
        items: dict[str, Any] = dict(self._sqlite.raw_items(collection))
        path = _snapshot_file(self._dir, collection)
        if not items:
            path.unlink(missing_ok=True)
            return
        path.write_text(
            yaml.safe_dump(items, sort_keys=True, default_flow_style=False),
            encoding="utf-8",
        )
