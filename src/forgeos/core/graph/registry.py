"""Typed edge registry (plan §6).

Each edge type declares which node types it may connect. ``None`` means "any node
type". Validation keeps the graph well-formed so traversal and ``why`` queries can
rely on edge semantics. Rules are intentionally small and explicit.
"""

from __future__ import annotations

from dataclasses import dataclass

from forgeos.core.graph.models import EdgeType, NodeType

_ANY: frozenset[NodeType] | None = None


@dataclass(frozen=True)
class EdgeRule:
    """Allowed source/destination node types for an edge type."""

    src: frozenset[NodeType] | None
    dst: frozenset[NodeType] | None


_REGISTRY: dict[EdgeType, EdgeRule] = {
    EdgeType.CONTAINS: EdgeRule(frozenset({NodeType.MODULE}), frozenset({NodeType.FILE})),
    EdgeType.DEPENDS_ON: EdgeRule(
        frozenset({NodeType.MODULE, NodeType.FILE}),
        frozenset({NodeType.MODULE, NodeType.DEPENDENCY}),
    ),
    EdgeType.DECIDED_BY: EdgeRule(
        frozenset({NodeType.FILE, NodeType.MODULE}), frozenset({NodeType.DECISION})
    ),
    EdgeType.AFFECTS: EdgeRule(
        frozenset({NodeType.DECISION}), frozenset({NodeType.FILE, NodeType.MODULE})
    ),
    EdgeType.SUPERSEDES: EdgeRule(
        frozenset({NodeType.DECISION}), frozenset({NodeType.DECISION})
    ),
    EdgeType.SUMMARIZED_BY: EdgeRule(_ANY, frozenset({NodeType.KNOWLEDGE_CARD})),
    EdgeType.USES_SKILL: EdgeRule(
        frozenset({NodeType.AGENT, NodeType.PROJECT}), frozenset({NodeType.SKILL})
    ),
    EdgeType.DERIVED_FROM: EdgeRule(frozenset({NodeType.MEMORY_REF}), _ANY),
    EdgeType.RELATES_TO: EdgeRule(_ANY, _ANY),
    # Advisory System (ADR 0010)
    EdgeType.ADVISES: EdgeRule(
        frozenset({NodeType.MENTOR_RECOMMENDATION}),
        frozenset({NodeType.FILE, NodeType.MODULE, NodeType.PROJECT, NodeType.DECISION}),
    ),
    EdgeType.INFORMS: EdgeRule(
        frozenset({NodeType.MENTOR_RECOMMENDATION}), frozenset({NodeType.DECISION})
    ),
    EdgeType.AUDITS: EdgeRule(
        frozenset({NodeType.AUDIT_FINDING}),
        frozenset({NodeType.FILE, NodeType.MODULE, NodeType.PROJECT, NodeType.DECISION}),
    ),
}


def is_edge_allowed(edge_type: EdgeType, src: NodeType, dst: NodeType) -> bool:
    """Return whether an edge of ``edge_type`` may connect ``src`` to ``dst``."""
    rule = _REGISTRY[edge_type]
    if rule.src is not None and src not in rule.src:
        return False
    return not (rule.dst is not None and dst not in rule.dst)


def validate_edge(edge_type: EdgeType, src: NodeType, dst: NodeType) -> None:
    """Raise :class:`ValueError` if the edge violates the registry."""
    if not is_edge_allowed(edge_type, src, dst):
        raise ValueError(
            f"edge {edge_type.value} not allowed from {src.value} to {dst.value}"
        )
