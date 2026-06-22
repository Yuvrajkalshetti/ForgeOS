"""Helpers for locating and describing the golden repository corpus."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

GOLDEN_ROOT = Path(__file__).parent / "golden"


def golden_root() -> Path:
    """Return the corpus root directory."""
    return GOLDEN_ROOT


def load_manifest() -> dict[str, Any]:
    """Return the parsed ``MANIFEST.yaml``."""
    text = (GOLDEN_ROOT / "MANIFEST.yaml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    assert isinstance(data, dict)
    return data


def corpus_path(name: str) -> Path:
    """Return the root path of a named corpus (``small``/``medium``/``monorepo``)."""
    manifest = load_manifest()
    corpora = manifest["corpora"]
    if name not in corpora:
        raise KeyError(f"unknown corpus: {name!r}")
    return GOLDEN_ROOT / corpora[name]["root"]
