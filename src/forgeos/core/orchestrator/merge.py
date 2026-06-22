"""Deterministic merge of agent findings.

Findings are collected from successful agents, de-duplicated by (agent, claim), and
sorted by a stable key — severity, then descending confidence, then agent, then
claim — so the merged output is identical regardless of completion order.
"""

from __future__ import annotations

from forgeos.core.orchestrator.agents import Finding

_SEVERITY_RANK = {"high": 0, "med": 1, "low": 2}


def _sort_key(finding: Finding) -> tuple[int, float, str, str]:
    return (
        _SEVERITY_RANK.get(finding.severity, 3),
        -finding.confidence,
        finding.agent,
        finding.claim,
    )


def merge_findings(findings: list[Finding]) -> list[Finding]:
    """Return de-duplicated findings in a deterministic, stable order."""
    unique: dict[tuple[str, str], Finding] = {}
    for finding in findings:
        unique.setdefault((finding.agent, finding.claim), finding)
    return sorted(unique.values(), key=_sort_key)
