"""Knowledge graph domain models (plan §6).

A generic property graph: typed nodes and typed edges with free-form ``props``.
Identity is explicit string ids so deterministic producers (RepoIntel, P4) can
assign stable ids and re-ingest idempotently.
"""

from __future__ import annotations

import datetime
from enum import Enum

from pydantic import BaseModel, Field

from forgeos._ids import new_id
from forgeos._time import utcnow


class NodeType(str, Enum):
    FILE = "File"
    MODULE = "Module"
    DEPENDENCY = "Dependency"
    DECISION = "Decision"
    SKILL = "Skill"
    AGENT = "Agent"
    PROJECT = "Project"
    MEMORY_REF = "MemoryRef"
    KNOWLEDGE_CARD = "KnowledgeCard"
    MENTOR_RECOMMENDATION = "MentorRecommendation"  # Advisory System (ADR 0010)
    AUDIT_FINDING = "AuditFinding"  # Advisory System (ADR 0010)


class EdgeType(str, Enum):
    DEPENDS_ON = "depends_on"
    CONTAINS = "contains"
    DECIDED_BY = "decided_by"
    AFFECTS = "affects"
    SUPERSEDES = "supersedes"
    SUMMARIZED_BY = "summarized_by"
    USES_SKILL = "uses_skill"
    DERIVED_FROM = "derived_from"
    RELATES_TO = "relates_to"
    ADVISES = "advises"  # MentorRecommendation -> subject (ADR 0010)
    INFORMS = "informs"  # MentorRecommendation -> Decision (ADR 0010)
    AUDITS = "audits"  # AuditFinding -> subject (ADR 0010)


class Node(BaseModel):
    """A typed graph node."""

    id: str = Field(default_factory=lambda: new_id("node"))
    type: NodeType
    label: str
    props: dict[str, object] = Field(default_factory=dict)
    created_at: datetime.datetime = Field(default_factory=utcnow)
    updated_at: datetime.datetime = Field(default_factory=utcnow)


class Edge(BaseModel):
    """A typed, directed edge between two nodes."""

    id: str = Field(default_factory=lambda: new_id("edge"))
    src_id: str
    dst_id: str
    type: EdgeType
    props: dict[str, object] = Field(default_factory=dict)
    created_at: datetime.datetime = Field(default_factory=utcnow)
