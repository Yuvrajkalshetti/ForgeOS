"""Sibling store for Data Flow Intelligence (ADR 0017).

Reads/writes ``df_nodes`` / ``df_edges`` over a ``StoragePort`` — isolated from the V1 and
exec-intel collections. Edges reference exec function/method node ids by convention.
"""

from __future__ import annotations

from forgeos.core.dataflow_intel.models import DF_EDGES, DF_NODES, DfEdge, StateSymbol
from forgeos.ports.storage import StoragePort


class DataFlowStore:
    """Persist and query the data-flow (state) graph."""

    def __init__(self, store: StoragePort) -> None:
        self._store = store

    def put_node(self, node: StateSymbol) -> None:
        self._store.put(DF_NODES, node.id, node.model_dump(mode="json"))

    def put_edge(self, edge: DfEdge) -> None:
        self._store.put(DF_EDGES, edge.id, edge.model_dump(mode="json"))

    def get_node(self, node_id: str) -> StateSymbol | None:
        row = self._store.get(DF_NODES, node_id)
        return StateSymbol.model_validate(row) if row is not None else None

    def nodes(self) -> list[StateSymbol]:
        rows = self._store.query(DF_NODES)
        return sorted((StateSymbol.model_validate(r) for r in rows), key=lambda n: n.id)

    def edges(self) -> list[DfEdge]:
        rows = self._store.query(DF_EDGES)
        return sorted((DfEdge.model_validate(r) for r in rows), key=lambda e: e.id)

    def node_ids(self) -> set[str]:
        return {str(r["id"]) for r in self._store.query(DF_NODES)}

    def edge_ids(self) -> set[str]:
        return {str(r["id"]) for r in self._store.query(DF_EDGES)}

    def delete_node(self, node_id: str) -> None:
        self._store.delete(DF_NODES, node_id)

    def delete_edge(self, edge_id: str) -> None:
        self._store.delete(DF_EDGES, edge_id)

    def reconcile(self, nodes: dict[str, StateSymbol], edges: dict[str, DfEdge]) -> None:
        """Make the store exactly match ``nodes``/``edges`` (idempotent full sync)."""
        for node_id in self.node_ids() - nodes.keys():
            self.delete_node(node_id)
        for edge_id in self.edge_ids() - edges.keys():
            self.delete_edge(edge_id)
        for node in nodes.values():
            self.put_node(node)
        for edge in edges.values():
            self.put_edge(edge)
