from __future__ import annotations

import pytest

from forgeos.core.graph import EdgeType, NodeType, is_edge_allowed, validate_edge


def test_contains_module_to_file_allowed() -> None:
    assert is_edge_allowed(EdgeType.CONTAINS, NodeType.MODULE, NodeType.FILE)


def test_contains_file_to_file_rejected() -> None:
    assert not is_edge_allowed(EdgeType.CONTAINS, NodeType.FILE, NodeType.FILE)


def test_relates_to_is_unrestricted() -> None:
    assert is_edge_allowed(EdgeType.RELATES_TO, NodeType.SKILL, NodeType.PROJECT)


def test_summarized_by_any_to_card() -> None:
    assert is_edge_allowed(EdgeType.SUMMARIZED_BY, NodeType.MODULE, NodeType.KNOWLEDGE_CARD)
    assert not is_edge_allowed(EdgeType.SUMMARIZED_BY, NodeType.MODULE, NodeType.FILE)


def test_validate_edge_raises_on_violation() -> None:
    with pytest.raises(ValueError, match="not allowed"):
        validate_edge(EdgeType.AFFECTS, NodeType.FILE, NodeType.DECISION)
