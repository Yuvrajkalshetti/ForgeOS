"""Data Flow Intelligence engine (E5A, ADR 0017).

Scans Python files into the state graph: emits self-attribute READS/WRITES, and aggregates
the count-only resolution measurement (self / annotation / constructor / unresolved) that
gates E5B. Deterministic, provider-free, idempotent.
"""

from __future__ import annotations

from pathlib import Path

from forgeos.core.dataflow_intel.extract import extract_state
from forgeos.core.dataflow_intel.models import DataFlowScanResult, DfEdge, DfEdgeType, StateSymbol
from forgeos.core.dataflow_intel.store import DataFlowStore
from forgeos.core.repo_intel.scanner import iter_source_files


class DataFlowEngine:
    """Scan a repository's Python files into the state (READS/WRITES) graph."""

    def __init__(self, store: DataFlowStore) -> None:
        self._store = store

    def scan(self, root: Path) -> DataFlowScanResult:
        """Extract self-attr reads/writes + resolution stats from every Python file."""
        nodes: dict[str, StateSymbol] = {}
        edges: dict[str, DfEdge] = {}
        files = 0
        total = resolved_self = resolved_anno = resolved_ctor = unresolved = 0
        for sf in iter_source_files(root):
            if sf.language != "python":
                continue
            files += 1
            source = (root / sf.path).read_text(encoding="utf-8", errors="replace")
            ex = extract_state(sf.path, source)
            nodes.update(ex.nodes)
            for access in ex.accesses:
                edge = DfEdge(
                    id=f"{access.caller_id}|{access.edge.value}|{access.state_id}",
                    src_id=access.caller_id,
                    dst_id=access.state_id,
                    type=access.edge,
                )
                edges[edge.id] = edge
            total += ex.total_attr
            resolved_self += ex.resolved_self
            resolved_anno += ex.resolved_annotation
            resolved_ctor += ex.resolved_constructor
            unresolved += ex.unresolved

        self._store.reconcile(nodes, edges)
        resolved = resolved_self + resolved_anno + resolved_ctor
        return DataFlowScanResult(
            files=files,
            state_symbols=len(nodes),
            reads_edges=sum(1 for e in edges.values() if e.type is DfEdgeType.READS),
            writes_edges=sum(1 for e in edges.values() if e.type is DfEdgeType.WRITES),
            total_attribute_accesses=total,
            resolved_self=resolved_self,
            resolved_annotation=resolved_anno,
            resolved_constructor=resolved_ctor,
            unresolved_accesses=unresolved,
            resolution_rate=round(resolved / total, 2) if total else 0.0,
        )
