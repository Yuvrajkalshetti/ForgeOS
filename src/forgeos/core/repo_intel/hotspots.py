"""Hotspot analysis from git churn — git-optional and deterministic.

If a git history is available, ``git_churn`` counts how often each file changed.
Where git is unavailable (no repo, restricted environment), it returns ``{}`` and
hotspots are simply empty — analysis never fails and never calls a provider.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

from forgeos.core.repo_intel.models import Hotspot

ChurnSource = Callable[[Path], dict[str, int]]


def null_churn(root: Path) -> dict[str, int]:
    """A churn source that reports no history (deterministic default)."""
    return {}


def git_churn(root: Path) -> dict[str, int]:
    """Count per-file commit touches via ``git log``; ``{}`` if git is unavailable."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "log", "--name-only", "--pretty=format:"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    counts: dict[str, int] = {}
    for line in proc.stdout.splitlines():
        name = line.strip()
        if name:
            counts[name] = counts.get(name, 0) + 1
    return counts


def rank_hotspots(churn: dict[str, int], limit: int = 10) -> list[Hotspot]:
    """Return the most-changed files, sorted by churn desc then path."""
    ranked = sorted(churn.items(), key=lambda kv: (-kv[1], kv[0]))
    return [Hotspot(path=path, churn=count) for path, count in ranked[:limit]]
