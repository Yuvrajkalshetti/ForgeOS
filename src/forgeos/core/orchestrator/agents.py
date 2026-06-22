"""Agent definitions and the finding contract.

Five agents (Architect, Engineer, QA, Reviewer, Security). Each must produce
evidence-backed findings with a confidence and severity (plan §9).
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field

SEVERITIES = ("high", "med", "low")


class Finding(BaseModel):
    """An evidence-backed observation from an agent."""

    agent: str
    claim: str
    evidence: list[str] = Field(default_factory=list)
    confidence: float = 0.5
    severity: str = "low"
    alternatives: list[str] = Field(default_factory=list)


@dataclass(frozen=True)
class AgentSpec:
    """A declarative agent: a name and a system prompt."""

    name: str
    system_prompt: str


_CONTRACT = (
    " Respond ONLY with a JSON array of findings; each finding has: claim (string), "
    "evidence (array of strings), confidence (0..1), severity (high|med|low), "
    "alternatives (array of strings)."
)

DEFAULT_AGENTS: tuple[AgentSpec, ...] = (
    AgentSpec(
        "architect",
        "You are a software architect reviewing structure and design." + _CONTRACT,
    ),
    AgentSpec("engineer", "You are an engineer assessing implementation correctness." + _CONTRACT),
    AgentSpec("qa", "You are a QA engineer identifying test gaps and edge cases." + _CONTRACT),
    AgentSpec(
        "reviewer",
        "You are a code reviewer evaluating clarity and maintainability." + _CONTRACT,
    ),
    AgentSpec("security", "You are a security reviewer identifying risks." + _CONTRACT),
)
