"""Data Flow Intelligence engine (E5A/E5B.1, ADR 0017/0018).

Scans Python files into the state graph. Emits ``self.<attr>`` READS/WRITES directly, and
resolves typed cross-object accesses (annotation/constructor) by mapping the receiver type
name to its defining file via a unique class-name match — then emits the edge. Types not
defined in the repo are counted (in the resolution stats) but not edged. Deterministic,
provider-free, idempotent.
"""

from __future__ import annotations

from pathlib import Path

from forgeos.core.dataflow_intel.extract import StateExtractor, extract_state
from forgeos.core.dataflow_intel.models import (
    DataFlowScanResult,
    DfEdge,
    DfEdgeType,
    StateSymbol,
)
from forgeos.core.dataflow_intel.store import DataFlowStore
from forgeos.core.repo_intel.scanner import iter_source_files


class DataFlowEngine:
    """Scan a repository's Python files into the state (READS/WRITES) graph."""

    def __init__(self, store: DataFlowStore) -> None:
        self._store = store

    def scan(self, root: Path) -> DataFlowScanResult:
        """Emit self + typed reads/writes; report resolution stats. Idempotent."""
        extractors: list[StateExtractor] = []
        for sf in iter_source_files(root):
            if sf.language != "python":
                continue
            source = (root / sf.path).read_text(encoding="utf-8", errors="replace")
            extractors.append(extract_state(sf.path, source))

        class_files: dict[str, set[str]] = {}
        for ex in extractors:
            for name, file in ex.defined_classes.items():
                class_files.setdefault(name, set()).add(file)

        nodes: dict[str, StateSymbol] = {}
        edges: dict[str, DfEdge] = {}
        total = r_self = r_anno = r_ctor = unresolved = 0
        for ex in extractors:
            nodes.update(ex.nodes)
            for access in ex.accesses:
                self._add_edge(edges, access.caller_id, access.state_id, access.edge, "self")
            for typed in ex.typed:
                files = class_files.get(typed.type_name)
                if files is None or len(files) != 1:
                    continue  # external / ambiguous type: counted in stats, not edged
                target_file = next(iter(files))
                state_id = f"state:{target_file}#{typed.type_name}.{typed.attr}"
                nodes.setdefault(
                    state_id,
                    StateSymbol(
                        id=state_id,
                        kind="attr",
                        label=f"{typed.type_name}.{typed.attr}",
                        file=target_file,
                    ),
                )
                self._add_edge(edges, typed.caller_id, state_id, typed.edge, typed.source)
            total += ex.total_attr
            r_self += ex.resolved_self
            r_anno += ex.resolved_annotation
            r_ctor += ex.resolved_constructor
            unresolved += ex.unresolved

        self._store.reconcile(nodes, edges)
        resolved = r_self + r_anno + r_ctor
        return DataFlowScanResult(
            files=len(extractors),
            state_symbols=len(nodes),
            reads_edges=sum(1 for e in edges.values() if e.type is DfEdgeType.READS),
            writes_edges=sum(1 for e in edges.values() if e.type is DfEdgeType.WRITES),
            typed_edges=sum(1 for e in edges.values() if e.resolution != "self"),
            total_attribute_accesses=total,
            resolved_self=r_self,
            resolved_annotation=r_anno,
            resolved_constructor=r_ctor,
            unresolved_accesses=unresolved,
            resolution_rate=round(resolved / total, 2) if total else 0.0,
        )

    @staticmethod
    def _add_edge(
        edges: dict[str, DfEdge],
        caller_id: str,
        state_id: str,
        edge_type: DfEdgeType,
        resolution: str,
    ) -> None:
        edge = DfEdge(
            id=f"{caller_id}|{edge_type.value}|{state_id}",
            src_id=caller_id,
            dst_id=state_id,
            type=edge_type,
            resolution=resolution,
        )
        edges[edge.id] = edge
