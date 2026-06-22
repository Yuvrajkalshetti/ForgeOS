"""File walking, language detection, ignore rules, and content hashing.

Pure and deterministic: results are sorted by path and identity is a SHA-256 of
file bytes. No provider calls, no network.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from forgeos.core.repo_intel.models import ScannedFile

LANGUAGE_BY_EXT: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
}

DEFAULT_IGNORE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        ".forgeos",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
    }
)


def detect_language(path: Path) -> str | None:
    """Return the language for a file by extension, or ``None`` if unknown."""
    return LANGUAGE_BY_EXT.get(path.suffix.lower())


def _content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def iter_source_files(
    root: Path, ignore_dirs: frozenset[str] = DEFAULT_IGNORE_DIRS
) -> list[ScannedFile]:
    """Return recognized source files under ``root``, sorted by relative path."""
    found: list[ScannedFile] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in ignore_dirs for part in rel.parts):
            continue
        language = detect_language(path)
        if language is None:
            continue
        data = path.read_bytes()
        found.append(
            ScannedFile(
                path=rel.as_posix(),
                language=language,
                size=len(data),
                content_hash=_content_hash(data),
            )
        )
    return found
