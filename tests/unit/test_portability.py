from __future__ import annotations

from pathlib import Path

import pytest

from forgeos.adapters.storage.sqlite.snapshots import SnapshotStore
from forgeos.catalog import SCHEMA_VERSION
from forgeos.services.portability import backup, export_bundle, import_bundle


def _seed(snap_dir: Path) -> SnapshotStore:
    store = SnapshotStore.open(snap_dir)
    store.put("nodes", "n1", {"type": "File", "label": "a.py"})
    store.put("edges", "e1", {"type": "contains", "src": "n0", "dst": "n1"})
    store.put("memory", "m1", {"content": "remember"})
    return store


def test_export_import_round_trip_reproduces_records(tmp_path: Path) -> None:
    src_snap = tmp_path / "src"
    _seed(src_snap)

    bundle = export_bundle(src_snap, tmp_path / "bundle.tar.gz")
    assert bundle.exists()

    dst_snap = tmp_path / "restored"
    manifest = import_bundle(bundle, dst_snap)
    assert manifest.schema_version == SCHEMA_VERSION
    assert set(manifest.collections) == {"nodes", "edges", "memory"}

    restored = SnapshotStore.open(dst_snap)
    assert restored.get("nodes", "n1") == {"type": "File", "label": "a.py"}
    assert restored.get("edges", "e1") == {"type": "contains", "src": "n0", "dst": "n1"}
    assert restored.get("memory", "m1") == {"content": "remember"}


def test_import_rejects_newer_schema(tmp_path: Path) -> None:
    src_snap = tmp_path / "src"
    _seed(src_snap)
    bundle = export_bundle(src_snap, tmp_path / "b.tar.gz")

    # Forge a manifest claiming a future schema version.
    import io
    import json
    import tarfile

    forged = tmp_path / "forged.tar.gz"
    with tarfile.open(bundle, "r:gz") as src, tarfile.open(forged, "w:gz") as dst:
        for member in src.getmembers():
            extracted = src.extractfile(member)
            payload = extracted.read() if extracted else b""
            if member.name == "manifest.json":
                doc = json.loads(payload)
                doc["schema_version"] = SCHEMA_VERSION + 1
                payload = json.dumps(doc).encode("utf-8")
                member.size = len(payload)
            dst.addfile(member, io.BytesIO(payload))

    with pytest.raises(ValueError, match="newer than supported"):
        import_bundle(forged, tmp_path / "out")


def test_backup_creates_bundle_and_enforces_retention(tmp_path: Path) -> None:
    src_snap = tmp_path / "src"
    _seed(src_snap)
    backups = tmp_path / "backups"

    created = [backup(src_snap, backups, retention=3) for _ in range(5)]
    assert all(p.exists() for p in created[-3:])

    remaining = sorted(backups.glob("forgeos-knowledge-*.tar.gz"))
    assert len(remaining) == 3  # pruned to retention


def test_import_ignores_path_traversal_members(tmp_path: Path) -> None:
    import io
    import json
    import tarfile

    malicious = tmp_path / "evil.tar.gz"
    manifest = json.dumps(
        {"schema_version": SCHEMA_VERSION, "created_at": "now", "collections": []}
    ).encode("utf-8")
    with tarfile.open(malicious, "w:gz") as tar:
        info = tarfile.TarInfo("manifest.json")
        info.size = len(manifest)
        tar.addfile(info, io.BytesIO(manifest))
        evil = b"pwned"
        evil_info = tarfile.TarInfo("snapshots/../escape.yaml")
        evil_info.size = len(evil)
        tar.addfile(evil_info, io.BytesIO(evil))

    out = tmp_path / "out"
    import_bundle(malicious, out)
    assert not (tmp_path / "escape.yaml").exists()
    assert list(out.glob("*.yaml")) == []
