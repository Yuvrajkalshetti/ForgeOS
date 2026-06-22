"""Knowledge portability: export / import / backup.

Bundles are self-contained ``.tar.gz`` archives of the YAML snapshots plus a
``manifest.json`` recording the schema version — **never** the rebuildable SQLite
(plan §20/§22). Import validates the schema version and refuses bundles newer than
this runtime supports. ``backup`` writes timestamped bundles with rolling
retention (manual strategy; no scheduler in V1).
"""

from __future__ import annotations

import datetime
import io
import tarfile
from pathlib import Path

from pydantic import BaseModel

from forgeos.catalog import SCHEMA_VERSION

_MANIFEST_NAME = "manifest.json"
_SNAPSHOT_PREFIX = "snapshots/"
_BACKUP_STEM = "forgeos-knowledge"


class BundleManifest(BaseModel):
    """Metadata recorded at the root of every knowledge bundle."""

    schema_version: int
    created_at: str
    collections: list[str]


def _snapshot_files(snapshot_dir: Path) -> list[Path]:
    return sorted(snapshot_dir.glob("*.yaml"))


def export_bundle(snapshot_dir: Path, dest_path: Path) -> Path:
    """Write a bundle of ``snapshot_dir`` to ``dest_path`` and return it."""
    files = _snapshot_files(snapshot_dir)
    manifest = BundleManifest(
        schema_version=SCHEMA_VERSION,
        created_at=datetime.datetime.now(datetime.UTC).isoformat(),
        collections=[f.stem for f in files],
    )
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(dest_path, "w:gz") as tar:
        raw = manifest.model_dump_json(indent=2).encode("utf-8")
        info = tarfile.TarInfo(_MANIFEST_NAME)
        info.size = len(raw)
        tar.addfile(info, io.BytesIO(raw))
        for path in files:
            tar.add(path, arcname=f"{_SNAPSHOT_PREFIX}{path.name}")
    return dest_path


def _safe_snapshot_name(member_name: str) -> str | None:
    """Return the bare filename for a safe snapshot member, else ``None``."""
    if not member_name.startswith(_SNAPSHOT_PREFIX):
        return None
    relative = member_name[len(_SNAPSHOT_PREFIX) :]
    if not relative or "/" in relative or relative.startswith(".."):
        return None
    return relative


def import_bundle(bundle_path: Path, target_snapshot_dir: Path) -> BundleManifest:
    """Extract a bundle's snapshots into ``target_snapshot_dir`` after validation."""
    target_snapshot_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(bundle_path, "r:gz") as tar:
        manifest_member = tar.extractfile(_MANIFEST_NAME)
        if manifest_member is None:
            raise ValueError("bundle is missing manifest.json")
        manifest = BundleManifest.model_validate_json(manifest_member.read())
        if manifest.schema_version > SCHEMA_VERSION:
            raise ValueError(
                f"bundle schema_version {manifest.schema_version} is newer than "
                f"supported {SCHEMA_VERSION}; upgrade ForgeOS to import it"
            )
        for member in tar.getmembers():
            name = _safe_snapshot_name(member.name)
            if name is None:
                continue
            source = tar.extractfile(member)
            if source is not None:
                (target_snapshot_dir / name).write_bytes(source.read())
    return manifest


def backup(snapshot_dir: Path, backups_dir: Path, retention: int = 10) -> Path:
    """Write a timestamped bundle into ``backups_dir`` and prune to ``retention``."""
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%S%f")
    dest = backups_dir / f"{_BACKUP_STEM}-{stamp}.tar.gz"
    export_bundle(snapshot_dir, dest)

    existing = sorted(backups_dir.glob(f"{_BACKUP_STEM}-*.tar.gz"))
    for stale in existing[:-retention] if retention > 0 else []:
        stale.unlink(missing_ok=True)
    return dest
