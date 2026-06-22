"""Repository Intelligence — deterministic, provider-free repository ingest.

This package MUST NOT import ``forgeos.ports.provider`` or call any provider/LLM.
Scanning, dependency discovery, hotspot analysis, and incremental indexing are
pure static analysis (ADR 0005), enforced by a static import-guard test.
"""

from __future__ import annotations

from forgeos.core.repo_intel.engine import RepoIntelEngine
from forgeos.core.repo_intel.hotspots import null_churn, rank_hotspots
from forgeos.core.repo_intel.models import RepoProfile, ScannedFile, ScanResult
from forgeos.core.repo_intel.scanner import detect_language, iter_source_files

__all__ = [
    "RepoIntelEngine",
    "RepoProfile",
    "ScanResult",
    "ScannedFile",
    "detect_language",
    "iter_source_files",
    "null_churn",
    "rank_hotspots",
]
