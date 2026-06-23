"""Read-only queries over the Execution Intelligence call graph (E3, ADR 0015).

Pure traversal over ``CALLS`` edges with a confidence floor — no mutation, no provider.
Callers default (at the transport layer) to ``min_confidence=resolved`` so heuristic or
unresolved relationships are excluded unless explicitly requested.
"""

from __future__ import annotations

from forgeos.core.exec_intel.models import Confidence, ExecEdgeType
from forgeos.core.exec_intel.store import ExecGraphStore

_RANK: dict[Confidence, int] = {
    Confidence.UNRESOLVED: 0,
    Confidence.HEURISTIC: 1,
    Confidence.RESOLVED: 2,
    Confidence.EXACT: 3,
}


def resolve(store: ExecGraphStore, target: str) -> list[str]:
    """Resolve ``target`` (a node id, or an exact qualname label) to matching node ids."""
    if store.get_node(target) is not None:
        return [target]
    return sorted(n.id for n in store.nodes() if n.label == target)


def _adjacency(
    store: ExecGraphStore, min_conf: Confidence
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    floor = _RANK[min_conf]
    forward: dict[str, list[str]] = {}
    reverse: dict[str, list[str]] = {}
    for edge in store.edges():
        if edge.type is not ExecEdgeType.CALLS or _RANK[edge.confidence] < floor:
            continue
        forward.setdefault(edge.src_id, []).append(edge.dst_id)
        reverse.setdefault(edge.dst_id, []).append(edge.src_id)
    return forward, reverse


def _bfs(adj: dict[str, list[str]], start: str, depth: int) -> list[str]:
    visited: set[str] = {start}
    frontier = [start]
    found: list[str] = []
    for _ in range(depth):
        nxt: list[str] = []
        for node in frontier:
            for neighbor in sorted(adj.get(node, [])):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                nxt.append(neighbor)
                found.append(neighbor)
        frontier = sorted(nxt)
        if not frontier:
            break
    return found


def callees(store: ExecGraphStore, node_id: str, depth: int, min_conf: Confidence) -> list[str]:
    """Symbols transitively called by ``node_id`` (forward BFS, bounded by ``depth``)."""
    forward, _ = _adjacency(store, min_conf)
    return _bfs(forward, node_id, depth)


def callers(store: ExecGraphStore, node_id: str, depth: int, min_conf: Confidence) -> list[str]:
    """Symbols that transitively call ``node_id`` (reverse BFS, bounded by ``depth``)."""
    _, reverse = _adjacency(store, min_conf)
    return _bfs(reverse, node_id, depth)


def impact(store: ExecGraphStore, node_id: str, min_conf: Confidence) -> list[str]:
    """All transitive callers of ``node_id`` (unbounded reverse reachability)."""
    _, reverse = _adjacency(store, min_conf)
    return _bfs(reverse, node_id, len(reverse) + 1)


def paths_to(
    store: ExecGraphStore,
    node_id: str,
    max_depth: int,
    max_paths: int,
    min_conf: Confidence,
) -> list[list[str]]:
    """Caller chains that reach ``node_id`` (ordered root -> ... -> target), bounded."""
    _, reverse = _adjacency(store, min_conf)
    paths: list[list[str]] = []

    def walk(node: str, chain: list[str], depth: int) -> None:
        if len(paths) >= max_paths:
            return
        upstream = [c for c in sorted(reverse.get(node, [])) if c not in chain]
        if not upstream or depth >= max_depth:
            paths.append(list(reversed(chain)))
            return
        for caller in upstream:
            walk(caller, [*chain, caller], depth + 1)

    walk(node_id, [node_id], 0)
    return paths[:max_paths]
