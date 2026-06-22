from __future__ import annotations

from pathlib import Path

from forgeos.adapters.storage.sqlite.store import SqliteStorage
from forgeos.ports.storage import StoragePort


def test_satisfies_storage_protocol() -> None:
    assert isinstance(SqliteStorage.open(), StoragePort)


def test_put_get_delete() -> None:
    store = SqliteStorage.open()
    store.put("nodes", "n1", {"type": "File", "label": "a.py"})
    assert store.get("nodes", "n1") == {"type": "File", "label": "a.py"}
    store.delete("nodes", "n1")
    assert store.get("nodes", "n1") is None


def test_query_filters_and_collections() -> None:
    store = SqliteStorage.open()
    store.put("nodes", "n1", {"type": "File"})
    store.put("nodes", "n2", {"type": "Module"})
    store.put("edges", "e1", {"type": "contains"})
    assert len(store.query("nodes")) == 2
    assert [r["type"] for r in store.query("nodes", {"type": "Module"})] == ["Module"]
    assert store.collections() == ["edges", "nodes"]


def test_persists_across_reopen(tmp_path: Path) -> None:
    db = tmp_path / "forge.sqlite"
    store = SqliteStorage.open(db)
    store.put("memory", "m1", {"content": "hello"})
    store.close()

    reopened = SqliteStorage.open(db)
    assert reopened.get("memory", "m1") == {"content": "hello"}


def test_clear_empties_store() -> None:
    store = SqliteStorage.open()
    store.put("nodes", "n1", {"x": 1})
    store.clear()
    assert store.collections() == []
