"""``forge export | import | backup | init`` — portability + project init.

Thin transport wiring over the tested :mod:`forgeos.services.portability` functions.
Snapshots are the source of truth and live under ``<project>/.forgeos/snapshots``;
the SQLite index is rebuildable and lives under ``<project>/.forgeos/cache``.
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

import typer

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.services.portability import backup as backup_bundle
from forgeos.services.portability import export_bundle, import_bundle

_FORGEOS_DIR = ".forgeos"


def _snapshots(project: Path) -> Path:
    return project / _FORGEOS_DIR / "snapshots"


def _open(project: Path) -> SnapshotStore:
    db = project / _FORGEOS_DIR / "cache" / "forge.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    return SnapshotStore.open(_snapshots(project), db)


def export_cmd(dest: Path, project: Path = Path()) -> None:
    """Export the project's knowledge to a portable ``.tar.gz`` bundle."""
    bundle = export_bundle(_snapshots(project), dest)
    typer.echo(json.dumps({"bundle": str(bundle)}, indent=2))


def import_cmd(bundle: Path, project: Path = Path()) -> None:
    """Import a knowledge bundle into the project (snapshots are restored)."""
    try:
        manifest = import_bundle(bundle, _snapshots(project))
    except (ValueError, OSError, tarfile.TarError) as exc:
        typer.echo(json.dumps({"error": str(exc)}))
        raise typer.Exit(code=1) from exc
    _open(project)  # rebuild the SQLite index from the restored snapshots
    typer.echo(json.dumps(manifest.model_dump(mode="json"), indent=2))


def backup_cmd(project: Path = Path(), retention: int = 10) -> None:
    """Write a timestamped backup bundle and prune to ``--retention``."""
    backups_dir = project / _FORGEOS_DIR / "backups"
    dest = backup_bundle(_snapshots(project), backups_dir, retention=retention)
    typer.echo(json.dumps({"backup": str(dest), "retention": retention}, indent=2))


def init_cmd(project: Path = Path()) -> None:
    """Initialize a ForgeOS project. Idempotent; never overwrites existing data."""
    created = not (project / _FORGEOS_DIR).exists()
    store = _open(project)  # creates the layout; rebuilds index from any snapshots
    next_steps = [
        "forgeos doctor   # check provider, credentials, and setup",
        "forgeos scan     # ingest this repository into the knowledge graph",
        "forgeos wizard   # show the full getting-started walkthrough",
    ]
    typer.echo(
        json.dumps(
            {
                "project": str(project),
                "created": created,
                "snapshots": str(_snapshots(project)),
                "collections": sorted(store.collections()),
                "next_steps": next_steps,
            },
            indent=2,
        )
    )
