"""Execution Intelligence domain models (V2, ADR 0015).

A separate, namespaced symbol graph stored in its own collections (``exec_nodes`` /
``exec_edges``) so it never touches the V1 file/import graph. Identity is explicit and
stable (``func:<file>#<qualname>`` / ``class:<file>#<qualname>``) so re-extraction is
idempotent. Edges carry a ``confidence`` because static resolution is approximate.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field

from forgeos._time import utcnow

EXEC_NODES = "exec_nodes"
EXEC_EDGES = "exec_edges"


class ExecNodeType(str, Enum):
    FUNCTION = "Function"
    METHOD = "Method"
    CLASS = "Class"


class ExecEdgeType(str, Enum):
    DEFINES = "defines"
    EXTENDS = "extends"


class Confidence(str, Enum):
    EXACT = "exact"
    RESOLVED = "resolved"
    HEURISTIC = "heuristic"
    UNRESOLVED = "unresolved"


class ExecNode(BaseModel):
    """A code symbol: a function, method, or class."""

    id: str
    type: ExecNodeType
    label: str
    file: str
    lineno: int = 0
    props: dict[str, object] = Field(default_factory=dict)
    created_at: datetime.datetime = Field(default_factory=utcnow)
    updated_at: datetime.datetime = Field(default_factory=utcnow)


class ExecEdge(BaseModel):
    """A typed, directed edge between symbols (or from a V1 ``File`` node to a symbol)."""

    id: str
    src_id: str
    dst_id: str
    type: ExecEdgeType
    confidence: Confidence = Confidence.EXACT
    props: dict[str, object] = Field(default_factory=dict)
    created_at: datetime.datetime = Field(default_factory=utcnow)


@dataclass
class ExecScanResult:
    """Summary of an execution-intelligence scan (for callers/observability)."""

    files: int = 0
    functions: int = 0
    methods: int = 0
    classes: int = 0
    defines_edges: int = 0
    extends_edges: int = 0
