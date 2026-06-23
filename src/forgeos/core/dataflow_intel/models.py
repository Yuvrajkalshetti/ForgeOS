"""Data Flow Intelligence models (V2, E5A/E5B.1 — ADR 0017/0018).

State symbols are class attributes (``<Class>.<attr>``). READS/WRITES edges link a
function/method (exec node id) to a state symbol, tagged with how the receiver was
resolved: ``self`` (enclosing class), ``annotation`` (declared param/local type), or
``constructor`` (direct ``T()`` binding). Stored in their own ``df_nodes``/``df_edges``
collections, separate from the CALLS/DEFINES/EXTENDS graph.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field

from forgeos._time import utcnow

DF_NODES = "df_nodes"
DF_EDGES = "df_edges"


class DfEdgeType(str, Enum):
    READS = "reads"
    WRITES = "writes"


class StateSymbol(BaseModel):
    """A unit of state: a class attribute (``<Class>.<attr>``)."""

    id: str
    kind: str  # "attr"
    label: str
    file: str
    created_at: datetime.datetime = Field(default_factory=utcnow)


class DfEdge(BaseModel):
    """A READS or WRITES edge from a function/method (exec node id) to a state symbol."""

    id: str
    src_id: str
    dst_id: str
    type: DfEdgeType
    resolution: str = "self"  # self | annotation | constructor
    created_at: datetime.datetime = Field(default_factory=utcnow)


@dataclass
class DataFlowScanResult:
    """Summary of a data-flow scan, including the resolution-effectiveness measurement."""

    files: int = 0
    state_symbols: int = 0
    reads_edges: int = 0
    writes_edges: int = 0
    typed_edges: int = 0  # cross-object edges from annotation/constructor resolution
    # Resolution measurement over every ``recv.attr`` access.
    total_attribute_accesses: int = 0
    resolved_self: int = 0
    resolved_annotation: int = 0
    resolved_constructor: int = 0
    unresolved_accesses: int = 0
    resolution_rate: float = 0.0
