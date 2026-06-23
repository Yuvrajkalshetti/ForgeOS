"""Deterministic ownership classification (V2, E4 — ADR 0016).

Declared ownership comes from rule matching (symbol/name/path, by specificity);
observed ownership is the majority declared-domain of a symbol's direct (resolved)
callers, computed from the E2/E3 call graph. No provider, no inference. Confidence is
a documented deterministic blend of rule-tier weight and observed caller agreement.
"""

from __future__ import annotations

import fnmatch
import re

from forgeos.core.exec_intel.models import Confidence
from forgeos.core.exec_intel.query import callers
from forgeos.core.exec_intel.store import ExecGraphStore
from forgeos.core.ownership_intel.models import (
    UNCLASSIFIED,
    UNKNOWN,
    OwnershipResult,
    OwnershipRule,
)

_TIER_WEIGHT = {3: 1.0, 2: 0.8, 1: 0.6, 0: 0.2}
_TIER_NAME = {3: "symbol", 2: "name", 1: "path", 0: "default"}


def _match_tier(rule: OwnershipRule, label: str, file: str) -> int:
    if rule.match_kind == "symbol":
        return 3 if label == rule.pattern else 0
    if rule.match_kind == "name":
        return 2 if re.search(rule.pattern, label) is not None else 0
    if rule.match_kind == "path":
        return 1 if fnmatch.fnmatch(file, rule.pattern) else 0
    return 0


def _axes_for(label: str, file: str, rules: list[OwnershipRule]) -> dict[str, tuple[str, int]]:
    best: dict[str, tuple[str, int]] = {}
    for rule in rules:
        tier = _match_tier(rule, label, file)
        if tier == 0:
            continue
        for axis, value in (
            ("domain", rule.domain),
            ("layer", rule.layer),
            ("criticality", rule.criticality),
            ("impact", rule.impact),
        ):
            if value is None:
                continue
            current = best.get(axis)
            if current is None or tier > current[1]:
                best[axis] = (value, tier)
    return best


def declared_domain(store: ExecGraphStore, node_id: str, rules: list[OwnershipRule]) -> str:
    """Return the rule-declared domain for a symbol (``Unknown`` if no rule matches)."""
    node = store.get_node(node_id)
    if node is None:
        return UNKNOWN
    axes = _axes_for(node.label, node.file, rules)
    return axes["domain"][0] if "domain" in axes else UNKNOWN


def _observed(
    store: ExecGraphStore, node_id: str, rules: list[OwnershipRule]
) -> tuple[str, float, dict[str, int]]:
    counts: dict[str, int] = {}
    for caller_id in callers(store, node_id, 1, Confidence.RESOLVED):
        domain = declared_domain(store, caller_id, rules)
        if domain == UNKNOWN:
            continue
        counts[domain] = counts.get(domain, 0) + 1
    total = sum(counts.values())
    if total == 0:
        return UNKNOWN, 0.0, counts
    winner = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return winner, round(counts[winner] / total, 2), counts


def classify(store: ExecGraphStore, node_id: str, rules: list[OwnershipRule]) -> OwnershipResult:
    """Classify one symbol: declared (rules) + observed (call graph)."""
    node = store.get_node(node_id)
    label = node.label if node is not None else node_id
    file = node.file if node is not None else ""
    axes = _axes_for(label, file, rules)
    declared_owner, domain_tier = axes.get("domain", (UNKNOWN, 0))
    layer = axes.get("layer", (UNKNOWN, 0))[0]
    criticality = axes.get("criticality", (UNCLASSIFIED, 0))[0]
    impact = axes.get("impact", (UNCLASSIFIED, 0))[0]
    declared_conf = _TIER_WEIGHT[domain_tier] if declared_owner != UNKNOWN else 0.2

    observed_owner, observed_conf, caller_domains = _observed(store, node_id, rules)
    agreement = (
        declared_owner == observed_owner
        and UNKNOWN not in (declared_owner, observed_owner)
    )
    if caller_domains:
        boost = 0.1 if agreement else 0.0
        confidence = round(min(1.0, 0.5 * declared_conf + 0.5 * observed_conf + boost), 2)
    else:
        confidence = round(declared_conf, 2)

    return OwnershipResult(
        symbol=node_id,
        declared_owner=declared_owner,
        observed_owner=observed_owner,
        agreement=agreement,
        confidence=confidence,
        matched_by=_TIER_NAME[domain_tier],
        layer=layer,
        criticality=criticality,
        impact=impact,
        declared_confidence=round(declared_conf, 2),
        observed_confidence=observed_conf,
        caller_domains=caller_domains,
    )
