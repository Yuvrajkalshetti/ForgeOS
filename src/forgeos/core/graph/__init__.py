"""Knowledge graph: nodes/edges, a typed edge registry, and bounded traversal."""

from __future__ import annotations

from forgeos.core.graph.models import Edge, EdgeType, Node, NodeType
from forgeos.core.graph.registry import EdgeRule, is_edge_allowed, validate_edge
from forgeos.core.graph.store import GraphStore

__all__ = [
    "Edge",
    "EdgeRule",
    "EdgeType",
    "GraphStore",
    "Node",
    "NodeType",
    "is_edge_allowed",
    "validate_edge",
]
