"""CLI surface for portability: ``forge export | import | backup | init``.

Thin wiring over the tested ``services.portability`` functions and the snapshot store.
Covers each command, backup retention/pruning, init idempotency, and a full CLI
round-trip (export from one project, import into another).
"""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path

from typer.testing import CliRunner

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.adapters.transport.cli.app import app

runner = CliRunner()


def _store(project: Path) -> SnapshotStore:
    db = project / ".forgeos" / "cache" / "forge.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    return SnapshotStore.open(project / ".forgeos" / "snapshots", db)


def _seed(project: Path) -> None:
    store = _store(project)
    store.put("memory", "m1", {"content": "remember"})
    store.put("nodes", "n1", {"type": "File", "label": "a.py"})


# -- export ----------------------------------------------------------------------
def test_export_creates_bundle(tmp_path: Path) -> None:
    proj = tmp_path / "a"
    _seed(proj)
    dest = tmp_path / "bundle.tar.gz"
    result = runner.invoke(app, ["export", str(dest), "--project", str(proj)])
    assert result.exit_code == 0
    assert dest.exists()
    assert json.loads(result.stdout)["bundle"] == str(dest)


# -- import ----------------------------------------------------------------------
def test_import_restores_records(tmp_path: Path) -> None:
    proj_a = tmp_path / "a"
    _seed(proj_a)
    bundle = tmp_path / "bundle.tar.gz"
    runner.invoke(app, ["export", str(bundle), "--project", str(proj_a)])

    proj_b = tmp_path / "b"
    result = runner.invoke(app, ["import", str(bundle), "--project", str(proj_b)])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert set(payload["collections"]) == {"memory", "nodes"}
    # queryable after import (index rebuilt from restored snapshots)
    assert _store(proj_b).get("memory", "m1") == {"content": "remember"}


def test_import_bad_bundle_fails(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["import", str(tmp_path / "missing.tar.gz"), "--project", str(tmp_path / "b")]
    )
    assert result.exit_code == 1
    assert "error" in result.stdout


def test_import_rejects_newer_schema(tmp_path: Path) -> None:
    proj_a = tmp_path / "a"
    _seed(proj_a)
    good = tmp_path / "good.tar.gz"
    runner.invoke(app, ["export", str(good), "--project", str(proj_a)])

    forged = tmp_path / "forged.tar.gz"
    with tarfile.open(good, "r:gz") as src, tarfile.open(forged, "w:gz") as dst:
        for member in src.getmembers():
            extracted = src.extractfile(member)
            payload = extracted.read() if extracted else b""
            if member.name == "manifest.json":
                doc = json.loads(payload)
                doc["schema_version"] = doc["schema_version"] + 1
                payload = json.dumps(doc).encode("utf-8")
                member.size = len(payload)
            dst.addfile(member, io.BytesIO(payload))

    result = runner.invoke(app, ["import", str(forged), "--project", str(tmp_path / "b")])
    assert result.exit_code == 1
    assert "newer" in result.stdout


# -- backup ----------------------------------------------------------------------
def test_backup_creates_and_prunes(tmp_path: Path) -> None:
    proj = tmp_path / "a"
    _seed(proj)
    for _ in range(5):
        result = runner.invoke(app, ["backup", "--project", str(proj), "--retention", "3"])
        assert result.exit_code == 0
    backups = sorted((proj / ".forgeos" / "backups").glob("forgeos-knowledge-*.tar.gz"))
    assert len(backups) == 3  # pruned to retention


# -- init ------------------------------------------------------------------------
def test_init_creates_project_structure(tmp_path: Path) -> None:
    proj = tmp_path / "fresh"
    result = runner.invoke(app, ["init", "--project", str(proj)])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["created"] is True
    assert (proj / ".forgeos" / "snapshots").is_dir()


def test_init_is_idempotent_and_preserves_data(tmp_path: Path) -> None:
    proj = tmp_path / "p"
    runner.invoke(app, ["init", "--project", str(proj)])
    _seed(proj)  # add data after first init

    second = runner.invoke(app, ["init", "--project", str(proj)])
    assert second.exit_code == 0
    assert json.loads(second.stdout)["created"] is False  # already initialized
    # data not overwritten
    assert _store(proj).get("memory", "m1") == {"content": "remember"}


# -- round-trip workflow ---------------------------------------------------------
def test_cli_round_trip_init_export_import(tmp_path: Path) -> None:
    proj_a = tmp_path / "a"
    assert runner.invoke(app, ["init", "--project", str(proj_a)]).exit_code == 0
    _seed(proj_a)
    bundle = tmp_path / "rt.tar.gz"
    assert runner.invoke(app, ["export", str(bundle), "--project", str(proj_a)]).exit_code == 0

    proj_b = tmp_path / "b"
    assert runner.invoke(app, ["init", "--project", str(proj_b)]).exit_code == 0
    assert runner.invoke(app, ["import", str(bundle), "--project", str(proj_b)]).exit_code == 0

    assert _store(proj_b).get("nodes", "n1") == {"type": "File", "label": "a.py"}
