"""Context Assembly engine (plan §10).

Pipeline: resolve seed -> bounded graph expansion -> gather (cards before source) ->
**deterministic tier ranking** -> token-budget trim -> assemble bundle + manifest.
Records a token event so savings (raw-equivalent vs assembled) are accountable.
Deterministic; no embeddings or semantic search.

``assemble(scope_ref, items)`` is the reusable budgeting core: advisory grounding
(P6.6) gathers items from many sources and runs them through the same step.
"""

from __future__ import annotations

from pathlib import Path

from forgeos._ids import new_id
from forgeos.catalog import Collections
from forgeos.core.compression.generator import card_id_for
from forgeos.core.context_assembly.models import (
    ContextBundle,
    ContextItem,
    ManifestEntry,
    tier_for,
)
from forgeos.core.graph import GraphStore, Node, NodeType
from forgeos.core.token_intel.ledger import TokenLedger
from forgeos.ports.storage import StoragePort
from forgeos.ports.tokenizer import TokenizerPort

_MAX_SOURCE_CHARS = 8000


class ContextAssembler:
    """Assemble a budgeted, auditable context bundle for a target."""

    def __init__(
        self,
        graph: GraphStore,
        tokenizer: TokenizerPort,
        store: StoragePort,
        budget_tokens: int,
        ledger: TokenLedger | None = None,
    ) -> None:
        self._graph = graph
        self._tokenizer = tokenizer
        self._store = store
        self._budget = budget_tokens
        self._ledger = ledger

    def build(
        self, target: str, depth: int = 2, source_root: Path | None = None
    ) -> ContextBundle:
        """Build a context bundle for ``target`` (node id or label)."""
        seed = self._graph.get_node(target) or self._graph.find_by_label(target)
        if seed is None:
            return ContextBundle(target=target)
        candidates = self._unique([seed, *self._graph.traverse(seed.id, depth)])
        items: list[ContextItem] = []
        for order, node in enumerate(candidates):
            items.append(self._item(node, source_root, order))
        return self.assemble(seed.id, items)

    def assemble(self, scope_ref: str, items: list[ContextItem]) -> ContextBundle:
        """Rank by tier, trim to budget, build manifest, record savings."""
        ranked = sorted(items, key=lambda it: (it.tier, it.order, it.ref))
        bundle = ContextBundle(target=scope_ref)
        used = 0
        raw_equiv = 0
        for item in ranked:
            raw_equiv += item.raw_tokens
            if used + item.tokens <= self._budget:
                used += item.tokens
                bundle.items.append(item)
                bundle.manifest.append(self._entry(item, included=True, reason="included"))
            else:
                bundle.dropped.append(item.ref)
                bundle.manifest.append(
                    self._entry(item, included=False, reason="dropped:budget")
                )
        bundle.total_tokens = used
        if self._ledger is not None:
            self._ledger.record(
                request_id=new_id("req"),
                scope_ref=scope_ref,
                provider="context-assembly",
                model="n/a",
                tokens_estimated=used,
                tokens_raw_equiv=raw_equiv,
            )
        return bundle

    @staticmethod
    def _entry(item: ContextItem, *, included: bool, reason: str) -> ManifestEntry:
        return ManifestEntry(
            ref=item.ref, kind=item.kind, tokens=item.tokens,
            tier=item.tier, included=included, reason=reason,
        )

    @staticmethod
    def _unique(nodes: list[Node]) -> list[Node]:
        seen: set[str] = set()
        result: list[Node] = []
        for node in nodes:
            if node.id not in seen:
                seen.add(node.id)
                result.append(node)
        return result

    def _item(self, node: Node, source_root: Path | None, order: int) -> ContextItem:
        # Cards before source (AC11): a node's card wins; raw source only without a card.
        card = self._store.get(Collections.CARDS, card_id_for(node.type.value, node.id))
        if card is not None:
            content, kind = str(card.get("purpose", "")), "card"
        elif node.type == NodeType.FILE and source_root is not None:
            content, kind = self._read_source(source_root, node.label), "source"
        else:
            content, kind = node.label, "stub"
        tokens = self._tokenizer.count_text(content)
        return ContextItem(
            ref=node.id,
            kind=kind,
            content=content,
            tokens=tokens,
            raw_tokens=self._raw_tokens(node, source_root, tokens),
            tier=tier_for(kind),
            order=order,
        )

    def _raw_tokens(self, node: Node, source_root: Path | None, fallback: int) -> int:
        if node.type == NodeType.FILE:
            if source_root is not None:
                return self._tokenizer.count_text(self._read_source(source_root, node.label))
            raw_size = node.props.get("size", 0)
            size = int(raw_size) if isinstance(raw_size, int | float | str) else 0
            return max(fallback, (size + 3) // 4)
        return fallback

    @staticmethod
    def _read_source(source_root: Path, rel: str) -> str:
        try:
            text = (source_root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return rel
        return text[:_MAX_SOURCE_CHARS]
