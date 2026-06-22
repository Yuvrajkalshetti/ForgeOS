"""Sibling graph store for Execution Intelligence (ADR 0015).

Reads/writes ``exec_nodes`` / ``exec_edges`` over a ``StoragePort`` so the symbol graph
stays isolated from the V1 ``nodes``/``edges`` collections. No endpoint validation —
edges may reference V1 ``File`` node ids by convention.
"""

from __future__ import annotations

from forgeos.core.exec_intel.models import (
    EXEC_EDGES,
    EXEC_NODES,
    ExecEdge,
    ExecNode,
    ExecNodeType,
)
from forgeos.ports.storage import StoragePort


class ExecGraphStore:
    """Persist and query the execution-intelligence symbol graph."""

    def __init__(self, store: StoragePort) -> None:
        self._store = store

    def put_node(self, node: ExecNode) -> None:
        self._store.put(EXEC_NODES, node.id, node.model_dump(mode="json"))

    def put_edge(self, edge: ExecEdge) -> None:
        self._store.put(EXEC_EDGES, edge.id, edge.model_dump(mode="json"))

    def get_node(self, node_id: str) -> ExecNode | None:
        row = self._store.get(EXEC_NODES, node_id)
        return ExecNode.model_validate(row) if row is not None else None

    def nodes(self, node_type: ExecNodeType | None = None) -> list[ExecNode]:
        result = [ExecNode.model_validate(r) for r in self._store.query(EXEC_NODES)]
        if node_type is not None:
            result = [n for n in result if n.type == node_type]
        return sorted(result, key=lambda n: n.id)

    def edges(self) -> list[ExecEdge]:
        rows = self._store.query(EXEC_EDGES)
        return sorted((ExecEdge.model_validate(r) for r in rows), key=lambda e: e.id)

    def node_ids(self) -> set[str]:
        return {str(r["id"]) for r in self._store.query(EXEC_NODES)}

    def edge_ids(self) -> set[str]:
        return {str(r["id"]) for r in self._store.query(EXEC_EDGES)}

    def delete_node(self, node_id: str) -> None:
        self._store.delete(EXEC_NODES, node_id)

    def delete_edge(self, edge_id: str) -> None:
        self._store.delete(EXEC_EDGES, edge_id)

    def reconcile(self, nodes: dict[str, ExecNode], edges: dict[str, ExecEdge]) -> None:
        """Make the store exactly match ``nodes``/``edges`` (idempotent full sync)."""
        for node_id in self.node_ids() - nodes.keys():
            self.delete_node(node_id)
        for edge_id in self.edge_ids() - edges.keys():
            self.delete_edge(edge_id)
        for node in nodes.values():
            self.put_node(node)
        for edge in edges.values():
            self.put_edge(edge)
