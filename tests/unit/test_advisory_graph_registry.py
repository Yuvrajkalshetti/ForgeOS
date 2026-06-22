from __future__ import annotations

from forgeos.core.graph import EdgeType, NodeType, is_edge_allowed


def test_advises_targets_subjects() -> None:
    assert is_edge_allowed(EdgeType.ADVISES, NodeType.MENTOR_RECOMMENDATION, NodeType.MODULE)
    assert is_edge_allowed(EdgeType.ADVISES, NodeType.MENTOR_RECOMMENDATION, NodeType.DECISION)
    assert not is_edge_allowed(EdgeType.ADVISES, NodeType.MODULE, NodeType.FILE)


def test_informs_only_targets_decisions() -> None:
    assert is_edge_allowed(EdgeType.INFORMS, NodeType.MENTOR_RECOMMENDATION, NodeType.DECISION)
    assert not is_edge_allowed(EdgeType.INFORMS, NodeType.MENTOR_RECOMMENDATION, NodeType.FILE)


def test_audits_from_finding() -> None:
    assert is_edge_allowed(EdgeType.AUDITS, NodeType.AUDIT_FINDING, NodeType.FILE)
    assert not is_edge_allowed(EdgeType.AUDITS, NodeType.MENTOR_RECOMMENDATION, NodeType.FILE)


def test_new_node_type_values() -> None:
    assert NodeType.MENTOR_RECOMMENDATION.value == "MentorRecommendation"
    assert NodeType.AUDIT_FINDING.value == "AuditFinding"
