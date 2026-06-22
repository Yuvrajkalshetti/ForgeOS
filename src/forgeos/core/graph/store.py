"""Graph store over a :class:`~forgeos.ports.storage.StoragePort`.

Persistence is delegated to the store, so when backed by ``SnapshotStore`` the
graph is written through to ``nodes.yaml`` / ``edges.yaml`` automatically. Traversal
is bounded BFS with typed edge/node filters and deterministic ordering.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from enum import Enum

from forgeos._time import utcnow
from forgeos.catalog import Collections
from forgeos.core.graph.models import Edge, EdgeType, Node, NodeType
from forgeos.core.graph.registry import validate_edge
from forgeos.ports.storage import StoragePort

Clock = Callable[[], datetime.datetime]


class Direction(str, Enum):
    OUT = "out"
    IN = "in"
    BOTH = "both"


class GraphStore:
    """Create and traverse a typed knowledge graph."""

    def __init__(self, store: StoragePort, clock: Clock = utcnow) -> None:
        self._store = store
        self._clock = clock

    # -- nodes -----------------------------------------------------------------
    def upsert_node(
        self,
        node_type: NodeType,
        label: str,
        props: dict[str, object] | None = None,
        node_id: str | None = None,
    ) -> Node:
        """Insert or update a node. A stable ``node_id`` makes re-ingest idempotent."""
        now = self._clock()
        if node_id is None:
            node = Node(
                type=node_type, label=label, props=props or {}, created_at=now, updated_at=now
            )
        else:
            existing = self.get_node(node_id)
            node = Node(
                id=node_id,
                type=node_type,
                label=label,
                props=props or {},
                created_at=existing.created_at if existing is not None else now,
                updated_at=now,
            )
        self._store.put(Collections.NODES, node.id, node.model_dump(mode="json"))
        return node

    def get_node(self, node_id: str) -> Node | None:
        row = self._store.get(Collections.NODES, node_id)
        return Node.model_validate(row) if row is not None else None

    def remove_node(self, node_id: str) -> None:
        """Delete a node and every edge incident to it."""
        self._store.delete(Collections.NODES, node_id)
        incident = self._store.query(Collections.EDGES, {"src_id": node_id}) + (
            self._store.query(Collections.EDGES, {"dst_id": node_id})
        )
        for row in incident:
            self._store.delete(Collections.EDGES, str(row["id"]))

    def nodes(self, node_type: NodeType | None = None) -> list[Node]:
        rows = self._store.query(Collections.NODES)
        result = [Node.model_validate(row) for row in rows]
        if node_type is not None:
            result = [n for n in result if n.type == node_type]
        return sorted(result, key=lambda n: n.id)

    def find_by_label(self, label: str) -> Node | None:
        matches = [n for n in self.nodes() if n.label == label]
        return matches[0] if matches else None

    # -- edges -----------------------------------------------------------------
    def add_edge(
        self,
        src_id: str,
        dst_id: str,
        edge_type: EdgeType,
        props: dict[str, object] | None = None,
    ) -> Edge:
        """Add a validated edge. Idempotent for a given (src, dst, type)."""
        src = self.get_node(src_id)
        dst = self.get_node(dst_id)
        if src is None or dst is None:
            raise ValueError("both endpoints must exist before adding an edge")
        validate_edge(edge_type, src.type, dst.type)

        existing = self._find_edge(src_id, dst_id, edge_type)
        if existing is not None:
            return existing
        edge = Edge(
            src_id=src_id,
            dst_id=dst_id,
            type=edge_type,
            props=props or {},
            created_at=self._clock(),
        )
        self._store.put(Collections.EDGES, edge.id, edge.model_dump(mode="json"))
        return edge

    def edges(self) -> list[Edge]:
        return sorted(
            (Edge.model_validate(row) for row in self._store.query(Collections.EDGES)),
            key=lambda e: e.id,
        )

    # -- traversal -------------------------------------------------------------
    def neighbors(
        self,
        node_id: str,
        edge_types: list[EdgeType] | None = None,
        direction: Direction = Direction.OUT,
    ) -> list[tuple[Edge, Node]]:
        """Return ``(edge, neighbor)`` pairs, deterministically ordered by node id."""
        allowed = {e.value for e in edge_types} if edge_types else None
        pairs: list[tuple[Edge, Node]] = []
        if direction in (Direction.OUT, Direction.BOTH):
            for row in self._store.query(Collections.EDGES, {"src_id": node_id}):
                edge = Edge.model_validate(row)
                if allowed is None or edge.type.value in allowed:
                    other = self.get_node(edge.dst_id)
                    if other is not None:
                        pairs.append((edge, other))
        if direction in (Direction.IN, Direction.BOTH):
            for row in self._store.query(Collections.EDGES, {"dst_id": node_id}):
                edge = Edge.model_validate(row)
                if allowed is None or edge.type.value in allowed:
                    other = self.get_node(edge.src_id)
                    if other is not None:
                        pairs.append((edge, other))
        return sorted(pairs, key=lambda pair: pair[1].id)

    def traverse(
        self,
        start_id: str,
        max_depth: int = 2,
        edge_types: list[EdgeType] | None = None,
        node_types: list[NodeType] | None = None,
        direction: Direction = Direction.OUT,
    ) -> list[Node]:
        """Bounded BFS from ``start_id``. Returns reachable nodes in BFS order."""
        wanted = {t.value for t in node_types} if node_types else None
        visited: set[str] = {start_id}
        frontier: list[str] = [start_id]
        result: list[Node] = []
        for _ in range(max_depth):
            nxt: list[str] = []
            for node_id in frontier:
                for _edge, neighbor in self.neighbors(node_id, edge_types, direction):
                    if neighbor.id in visited:
                        continue
                    visited.add(neighbor.id)
                    nxt.append(neighbor.id)
                    if wanted is None or neighbor.type.value in wanted:
                        result.append(neighbor)
            frontier = sorted(nxt)
            if not frontier:
                break
        return result

    def why(self, target: str) -> list[Node]:
        """Return Decision nodes explaining ``target`` (id or label).

        Combines outgoing ``decided_by`` edges and incoming ``affects`` edges.
        """
        node = self.get_node(target) or self.find_by_label(target)
        if node is None:
            return []
        decisions: dict[str, Node] = {}
        for _edge, neighbor in self.neighbors(node.id, [EdgeType.DECIDED_BY], Direction.OUT):
            if neighbor.type == NodeType.DECISION:
                decisions[neighbor.id] = neighbor
        for _edge, neighbor in self.neighbors(node.id, [EdgeType.AFFECTS], Direction.IN):
            if neighbor.type == NodeType.DECISION:
                decisions[neighbor.id] = neighbor
        return sorted(decisions.values(), key=lambda n: n.id)

    def _find_edge(self, src_id: str, dst_id: str, edge_type: EdgeType) -> Edge | None:
        for row in self._store.query(
            Collections.EDGES, {"src_id": src_id, "dst_id": dst_id}
        ):
            edge = Edge.model_validate(row)
            if edge.type == edge_type:
                return edge
        return None
