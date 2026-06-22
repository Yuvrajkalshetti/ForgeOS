"""Deterministic, provider-free knowledge card generator (ADR 0009).

Cards are derived entirely from the knowledge graph and RepoProfile — no provider,
no LLM, no network. Generation is **lazy**: a stored card whose ``source_hash`` still
matches its target is reused; otherwise it is rebuilt, validated against the JSON
Schema, persisted, and linked via a ``summarized_by`` edge. Identical inputs always
produce an identical card.
"""

from __future__ import annotations

import datetime
import hashlib
from collections.abc import Callable
from typing import Any

from forgeos._time import utcnow
from forgeos.catalog import Collections
from forgeos.core.compression.models import CardTarget, KnowledgeCard, ProviderRef
from forgeos.core.compression.schema import validate_card
from forgeos.core.graph import EdgeType, GraphStore, Node, NodeType
from forgeos.core.graph.store import Direction
from forgeos.ports.storage import StoragePort

Clock = Callable[[], datetime.datetime]

_GENERATOR = ProviderRef(name="forgeos", model="deterministic")


def card_id_for(node_type: str, node_id: str) -> str:
    """Deterministic, single-card-per-target id."""
    return f"card:{node_type}:{node_id}"


class CardGenerator:
    """Build and cache knowledge cards deterministically from the graph."""

    def __init__(self, store: StoragePort, graph: GraphStore, clock: Clock = utcnow) -> None:
        self._store = store
        self._graph = graph
        self._clock = clock

    def compress(self, node_id: str) -> KnowledgeCard:
        """Return a card for ``node_id``, reusing a valid cached one (lazy)."""
        node = self._graph.get_node(node_id)
        if node is None:
            raise ValueError(f"unknown node: {node_id}")
        source_hash = self._source_hash(node)
        key = card_id_for(node.type.value, node.id)

        cached = self._store.get(Collections.CARDS, key)
        if cached is not None and cached.get("source_hash") == source_hash:
            return KnowledgeCard.model_validate(cached)

        card = KnowledgeCard(
            card_id=key,
            target=CardTarget(type=node.type.value, ref=node.id),
            generated_at=self._clock().isoformat(),
            source_hash=source_hash,
            provider=_GENERATOR,
            **self._body(node),
        )
        data = card.model_dump(mode="json")
        validate_card(data)
        self._store.put(Collections.CARDS, key, data)
        self._graph.upsert_node(NodeType.KNOWLEDGE_CARD, label=key, node_id=key)
        self._graph.add_edge(node.id, key, EdgeType.SUMMARIZED_BY)
        return card

    # -- deterministic body ----------------------------------------------------
    def _body(self, node: Node) -> dict[str, Any]:
        if node.type == NodeType.MODULE:
            return self._module_body(node)
        if node.type == NodeType.FILE:
            return self._file_body(node)
        return {
            "purpose": f"{node.type.value} '{node.label}'.",
            "modules": [],
            "dependencies": [],
            "key_decisions": self._decisions(node.id),
            "risks": [],
            "recent_changes": [],
            "extensions": {},
        }

    def _file_body(self, node: Node) -> dict[str, Any]:
        language = node.props.get("language", "unknown")
        size = node.props.get("size", 0)
        return {
            "purpose": f"{node.label}: {language} file ({size} bytes).",
            "modules": [],
            "dependencies": self._deps([node.id]),
            "key_decisions": self._decisions(node.id),
            "risks": self._risks(node.label),
            "recent_changes": self._changes(node.label),
            "extensions": {},
        }

    def _module_body(self, node: Node) -> dict[str, Any]:
        files = [
            child
            for _e, child in self._graph.neighbors(node.id, [EdgeType.CONTAINS], Direction.OUT)
        ]
        return {
            "purpose": f"Module '{node.label}' containing {len(files)} file(s).",
            "modules": [
                {"name": f.label, "role": str(f.props.get("language", "unknown"))} for f in files
            ],
            "dependencies": self._deps([f.id for f in files]),
            "key_decisions": self._decisions(node.id),
            "risks": [r for f in files for r in self._risks(f.label)],
            "recent_changes": [c for f in files for c in self._changes(f.label)],
            "extensions": {},
        }

    def _deps(self, file_ids: list[str]) -> list[dict[str, str]]:
        seen: dict[str, dict[str, str]] = {}
        for file_id in file_ids:
            deps = self._graph.neighbors(file_id, [EdgeType.DEPENDS_ON], Direction.OUT)
            for _edge, target in deps:
                kind = "internal" if target.type == NodeType.MODULE else "external"
                seen[target.label] = {"name": target.label, "kind": kind, "why": ""}
        return [seen[name] for name in sorted(seen)]

    def _decisions(self, node_id: str) -> list[dict[str, str]]:
        decisions: dict[str, dict[str, str]] = {}
        for _e, dec in self._graph.neighbors(node_id, [EdgeType.DECIDED_BY], Direction.OUT):
            if dec.type == NodeType.DECISION:
                decisions[dec.id] = {"summary": dec.label, "decision_node_id": dec.id}
        for _e, dec in self._graph.neighbors(node_id, [EdgeType.AFFECTS], Direction.IN):
            if dec.type == NodeType.DECISION:
                decisions[dec.id] = {"summary": dec.label, "decision_node_id": dec.id}
        return [decisions[k] for k in sorted(decisions)]

    def _hotspot_churn(self, path: str) -> int:
        profile = self._store.get(Collections.REPO_PROFILE, "profile")
        if not profile:
            return 0
        for hotspot in profile.get("hotspots", []):
            if hotspot.get("path") == path:
                return int(hotspot.get("churn", 0))
        return 0

    def _risks(self, path: str) -> list[dict[str, str]]:
        if self._hotspot_churn(path) > 0:
            return [{"description": f"{path} changes frequently (hotspot)", "severity": "med"}]
        return []

    def _changes(self, path: str) -> list[dict[str, str]]:
        churn = self._hotspot_churn(path)
        if churn > 0:
            return [{"summary": f"{churn} recent commits", "ref": path}]
        return []

    def _source_hash(self, node: Node) -> str:
        if node.type == NodeType.FILE:
            return str(node.props.get("hash", ""))
        if node.type == NodeType.MODULE:
            children = self._graph.neighbors(node.id, [EdgeType.CONTAINS], Direction.OUT)
            parts = [f"{child.id}:{child.props.get('hash', '')}" for _edge, child in children]
            return hashlib.sha256("\n".join(sorted(parts)).encode()).hexdigest()
        return ""
