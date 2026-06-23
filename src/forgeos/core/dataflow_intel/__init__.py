"""Data Flow Intelligence (V2, E5A — ADR 0017): self-attribute reads/writes + a
count-only resolution-effectiveness measurement that gates E5B."""

from __future__ import annotations

from forgeos.core.dataflow_intel.engine import DataFlowEngine
from forgeos.core.dataflow_intel.models import (
    DataFlowScanResult,
    DfEdge,
    DfEdgeType,
    StateSymbol,
)
from forgeos.core.dataflow_intel.store import DataFlowStore

__all__ = [
    "DataFlowEngine",
    "DataFlowScanResult",
    "DataFlowStore",
    "DfEdge",
    "DfEdgeType",
    "StateSymbol",
]
