from __future__ import annotations

from pathlib import Path

import yaml

from forgeos.adapters.storage.sqlite.snapshots import SnapshotStore, load_snapshots
from forgeos.ports.storage import StoragePort


def test_satisfies_storage_protocol(tmp_path: Path) -> None:
    store = SnapshotStore.open(tmp_path / "snap")
    assert isinstance(store, StoragePort)


def test_put_writes_yaml_snapshot(tmp_path: Path) -> None:
    snap = tmp_path / "snap"
    store = SnapshotStore.open(snap)
    store.put("nodes", "n1", {"type": "File", "label": "a.py"})

    snapshot_file = snap / "nodes.yaml"
    assert snapshot_file.exists()
    data = yaml.safe_load(snapshot_file.read_text())
    assert data == {"n1": {"type": "File", "label": "a.py"}}


def test_delete_updates_snapshot_and_removes_empty_file(tmp_path: Path) -> None:
    snap = tmp_path / "snap"
    store = SnapshotStore.open(snap)
    store.put("nodes", "n1", {"x": 1})
    store.delete("nodes", "n1")
    assert not (snap / "nodes.yaml").exists()


def test_open_rebuilds_index_from_snapshots(tmp_path: Path) -> None:
    snap = tmp_path / "snap"
    store = SnapshotStore.open(snap)
    store.put("memory", "m1", {"content": "persisted"})

    # A brand-new in-memory index, opened on the same snapshot dir, must recover.
    reopened = SnapshotStore.open(snap)
    assert reopened.get("memory", "m1") == {"content": "persisted"}


def test_snapshot_is_source_of_truth_on_divergence(tmp_path: Path) -> None:
    snap = tmp_path / "snap"
    store = SnapshotStore.open(snap)
    store.put("nodes", "n1", {"v": "from-sqlite"})

    # Simulate divergence: hand-edit the YAML snapshot (the canonical source).
    (snap / "nodes.yaml").write_text(
        yaml.safe_dump({"n1": {"v": "from-yaml"}}), encoding="utf-8"
    )
    store.rebuild_index()
    assert store.get("nodes", "n1") == {"v": "from-yaml"}


def test_load_snapshots_reads_all_collections(tmp_path: Path) -> None:
    snap = tmp_path / "snap"
    store = SnapshotStore.open(snap)
    store.put("nodes", "n1", {"a": 1})
    store.put("edges", "e1", {"b": 2})
    loaded = load_snapshots(snap)
    assert loaded == {"nodes": {"n1": {"a": 1}}, "edges": {"e1": {"b": 2}}}
