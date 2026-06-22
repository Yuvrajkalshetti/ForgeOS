"""Knowledge card models (plan §9.1).

Fixed required core + open ``extensions`` for project-defined ``x_*`` blocks.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CardTarget(BaseModel):
    type: str
    ref: str


class ProviderRef(BaseModel):
    name: str
    model: str


class CardModule(BaseModel):
    name: str
    role: str = ""


class CardDependency(BaseModel):
    name: str
    kind: str = "external"  # internal | external
    why: str = ""


class CardDecision(BaseModel):
    summary: str
    decision_node_id: str | None = None


class CardRisk(BaseModel):
    description: str
    severity: str = "low"  # low | med | high


class CardChange(BaseModel):
    summary: str
    ref: str | None = None


class KnowledgeCard(BaseModel):
    """A compact, reusable summary of a repo/module/file/subsystem."""

    schema_version: int = 1
    card_id: str
    target: CardTarget
    generated_at: str
    source_hash: str
    provider: ProviderRef
    purpose: str
    modules: list[CardModule] = Field(default_factory=list)
    dependencies: list[CardDependency] = Field(default_factory=list)
    key_decisions: list[CardDecision] = Field(default_factory=list)
    risks: list[CardRisk] = Field(default_factory=list)
    recent_changes: list[CardChange] = Field(default_factory=list)
    extensions: dict[str, Any] = Field(default_factory=dict)
