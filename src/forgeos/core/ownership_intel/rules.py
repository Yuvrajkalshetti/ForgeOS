"""Load ownership rules: bundled generic defaults + the project's ownership.yaml.

Pure config loading — no provider, no inference. Project rules (from
``<project>/.forgeos/ownership.yaml``) take precedence over the bundled defaults
(same-tier ties resolve by order: project first). The trading/domain taxonomy lives
in the project file, not in ForgeOS core.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from forgeos.core.ownership_intel.models import OwnershipRule

_MATCH_KINDS = ("symbol", "name", "path")

# Generic, conservative layer hints by common directory; domains are project-supplied.
DEFAULT_RULES: tuple[OwnershipRule, ...] = (
    OwnershipRule(match_kind="path", pattern="*/routes/*", layer="Route"),
    OwnershipRule(match_kind="path", pattern="*/models/*", layer="Model"),
    OwnershipRule(match_kind="path", pattern="*/db/*", layer="Storage"),
    OwnershipRule(match_kind="path", pattern="*/services/*", layer="Service"),
)


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _rule_from_entry(entry: object) -> OwnershipRule | None:
    if not isinstance(entry, dict):
        return None
    match = entry.get("match")
    if not isinstance(match, dict):
        return None
    for kind in _MATCH_KINDS:
        pattern = match.get(kind)
        if isinstance(pattern, str):
            return OwnershipRule(
                match_kind=kind,
                pattern=pattern,
                domain=_str_or_none(entry.get("domain")),
                layer=_str_or_none(entry.get("layer")),
                criticality=_str_or_none(entry.get("criticality")),
                impact=_str_or_none(entry.get("impact")),
            )
    return None


def load_rules(project: Path) -> list[OwnershipRule]:
    """Return project rules (highest precedence) followed by bundled defaults."""
    project_rules: list[OwnershipRule] = []
    path = project / ".forgeos" / "ownership.yaml"
    if path.is_file():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        raw = data.get("rules") if isinstance(data, dict) else None
        if isinstance(raw, list):
            for entry in raw:
                rule = _rule_from_entry(entry)
                if rule is not None:
                    project_rules.append(rule)
    return [*project_rules, *DEFAULT_RULES]
