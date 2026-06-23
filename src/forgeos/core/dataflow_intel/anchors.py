"""Named data-flow anchors: map domain concepts (LTP, MTM) to symbols (E5B.2, ADR 0019).

Loaded from ``<project>/.forgeos/dataflow.yaml`` (``anchors:`` name -> symbol id or label).
Pure config; the trading vocabulary lives in the project, not ForgeOS core.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def load_anchors(project: Path) -> dict[str, str]:
    """Return the project's data-flow anchors (concept name -> symbol id/label)."""
    anchors: dict[str, str] = {}
    path = project / ".forgeos" / "dataflow.yaml"
    if path.is_file():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        raw = data.get("anchors") if isinstance(data, dict) else None
        if isinstance(raw, dict):
            for name, target in raw.items():
                if isinstance(name, str) and isinstance(target, str):
                    anchors[name] = target
    return anchors
