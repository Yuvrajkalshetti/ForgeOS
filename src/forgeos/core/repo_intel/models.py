"""Repository Intelligence data models."""

from __future__ import annotations

from dataclasses import dataclass, field

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class ScannedFile:
    """A discovered source file (transient)."""

    path: str  # POSIX path relative to the repo root
    language: str | None
    size: int
    content_hash: str


class FileRecord(BaseModel):
    """Cached per-file parse result (persisted in the repo_index collection)."""

    path: str
    hash: str
    language: str | None
    size: int
    raw_imports: list[str] = Field(default_factory=list)


class Hotspot(BaseModel):
    """A frequently-changed file (from churn analysis)."""

    path: str
    churn: int


class RepoProfile(BaseModel):
    """Compact repository summary feeding Compression + ranking (plan §8)."""

    root: str
    languages: list[str] = Field(default_factory=list)
    file_count: int = 0
    module_count: int = 0
    hotspots: list[Hotspot] = Field(default_factory=list)
    scanned_at: str = ""
    index_hash: str = ""


@dataclass
class ScanResult:
    """Outcome of a scan (for CLI/observability)."""

    files: int = 0
    modules: int = 0
    internal_edges: int = 0
    external_deps: int = 0
    parsed: int = 0
    reused: int = 0
    removed: int = 0
    hotspots: list[str] = field(default_factory=list)
