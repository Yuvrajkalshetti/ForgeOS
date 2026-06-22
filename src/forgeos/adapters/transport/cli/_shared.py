"""Shared helpers for CLI commands."""

from __future__ import annotations

from pathlib import Path

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.config.models import ForgeConfig


def open_store(project: Path) -> SnapshotStore:
    """Open the project's snapshot-backed store under ``<project>/.forgeos``."""
    db = project / ".forgeos" / "cache" / "forge.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    return SnapshotStore.open(project / ".forgeos" / "snapshots", db)


def provider_model(config: ForgeConfig) -> str:
    """Resolve the model name for the configured default provider."""
    default = config.providers.default
    if default == "claude":
        return config.providers.claude.model
    if default == "ollama":
        return config.providers.ollama.model
    return default
