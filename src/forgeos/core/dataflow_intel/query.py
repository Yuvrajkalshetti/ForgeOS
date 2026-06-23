"""Read-only queries over the state (READS/WRITES) graph (E5A, ADR 0017).

Pure traversal — no mutation, no provider. ``data_flow`` / ``flow_impact`` reach across to
the exec CALLS graph (E2/E3) to include the transitive callers of readers/writers.
"""

from __future__ import annotations

from forgeos.core.dataflow_intel.models import DfEdgeType
from forgeos.core.dataflow_intel.store import DataFlowStore
from forgeos.core.exec_intel.models import Confidence
from forgeos.core.exec_intel.query import callers as exec_callers
from forgeos.core.exec_intel.store import ExecGraphStore


def resolve(store: DataFlowStore, target: str) -> list[str]:
    """Resolve ``target`` (a state id or exact ``<Class>.<attr>`` label) to node ids."""
    if store.get_node(target) is not None:
        return [target]
    return sorted(n.id for n in store.nodes() if n.label == target)


def readers(store: DataFlowStore, state_id: str) -> list[str]:
    return sorted(
        {e.src_id for e in store.edges() if e.type is DfEdgeType.READS and e.dst_id == state_id}
    )


def writers(store: DataFlowStore, state_id: str) -> list[str]:
    return sorted(
        {e.src_id for e in store.edges() if e.type is DfEdgeType.WRITES and e.dst_id == state_id}
    )


def _with_callers(exec_store: ExecGraphStore, seeds: list[str]) -> list[str]:
    result = set(seeds)
    for seed in seeds:
        result.update(exec_callers(exec_store, seed, 6, Confidence.RESOLVED))
    return sorted(result)


def data_flow(
    df_store: DataFlowStore, exec_store: ExecGraphStore, state_id: str
) -> dict[str, list[str]]:
    """Upstream (writers + their callers) and downstream (readers + their callers)."""
    return {
        "upstream": _with_callers(exec_store, writers(df_store, state_id)),
        "downstream": _with_callers(exec_store, readers(df_store, state_id)),
    }


def flow_impact(
    df_store: DataFlowStore, exec_store: ExecGraphStore, state_id: str
) -> list[str]:
    """All symbols affected by a state symbol: readers/writers + their transitive callers."""
    seeds = readers(df_store, state_id) + writers(df_store, state_id)
    return _with_callers(exec_store, seeds)
