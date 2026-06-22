"""Agent orchestration: parallel, bounded, failure-isolated, deterministic merge."""

from __future__ import annotations

from forgeos.core.orchestrator.agents import DEFAULT_AGENTS, AgentSpec, Finding
from forgeos.core.orchestrator.merge import merge_findings
from forgeos.core.orchestrator.runner import AgentResult, Orchestrator, OrchestratorReport

__all__ = [
    "DEFAULT_AGENTS",
    "AgentResult",
    "AgentSpec",
    "Finding",
    "Orchestrator",
    "OrchestratorReport",
    "merge_findings",
]
