"""Cross-graph lineage: trace flow over CALLS + READS/WRITES (E5B.2, ADR 0019).

A forward directed graph combines the exec CALLS graph (caller -> callee), data WRITES
(producer -> state) and data READS (state -> consumer), so "how does X reach Y" is a bounded
path search. Deterministic, provider-free; no SSA, symbolic execution, or inference.
"""

from __future__ import annotations

from forgeos.core.dataflow_intel.models import DfEdgeType
from forgeos.core.dataflow_intel.store import DataFlowStore
from forgeos.core.exec_intel.models import Confidence, ExecEdgeType
from forgeos.core.exec_intel.store import ExecGraphStore

_RANK: dict[Confidence, int] = {
    Confidence.UNRESOLVED: 0,
    Confidence.HEURISTIC: 1,
    Confidence.RESOLVED: 2,
    Confidence.EXACT: 3,
}


def forward_adjacency(
    exec_store: ExecGraphStore, df_store: DataFlowStore, min_conf: Confidence
) -> dict[str, list[str]]:
    """Forward graph: CALLS (caller->callee), WRITES (func->state), READS (state->func)."""
    adj: dict[str, list[str]] = {}
    floor = _RANK[min_conf]
    for edge in exec_store.edges():
        if edge.type is ExecEdgeType.CALLS and _RANK[edge.confidence] >= floor:
            adj.setdefault(edge.src_id, []).append(edge.dst_id)
    for edge in df_store.edges():
        if edge.type is DfEdgeType.WRITES:
            adj.setdefault(edge.src_id, []).append(edge.dst_id)
        elif edge.type is DfEdgeType.READS:
            adj.setdefault(edge.dst_id, []).append(edge.src_id)
    return {key: sorted(set(values)) for key, values in adj.items()}


def find_paths(
    adj: dict[str, list[str]],
    source: str,
    target: str,
    max_depth: int,
    max_paths: int,
) -> list[list[str]]:
    """Bounded directed paths from ``source`` to ``target`` over ``adj``."""
    paths: list[list[str]] = []

    def walk(node: str, path: list[str], depth: int) -> None:
        if len(paths) >= max_paths:
            return
        if node == target:
            paths.append(path)
            return
        if depth >= max_depth:
            return
        for nxt in adj.get(node, []):
            if nxt not in path:
                walk(nxt, [*path, nxt], depth + 1)

    walk(source, [source], 0)
    return paths
