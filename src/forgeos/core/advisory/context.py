"""Advisory context builder (P6.6).

Grounds Mentor/Auditor in existing ForgeOS knowledge by composing a single,
token-budgeted :class:`ContextBundle` from existing components — **no new storage,
graph, provider, vectors, embeddings, or semantic retrieval**. It reuses Context
Assembly (budgeting/manifest/savings) and Token Intelligence.

Deterministic. **Provider-free** (it never calls an LLM; only Mentor/Auditor do).

Ranking is by deterministic priority tiers (``context_assembly.models.TIER``). Gather
order within a tier is **graph-reachable first, then recent-N fill**. Per AC11, a
subject's content escalates Card → Memory → Source, and raw source is used only when
a card is missing/stale or source is explicitly allowed.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from pathlib import Path

from forgeos._time import utcnow
from forgeos.catalog import Collections
from forgeos.core.compression.generator import card_id_for
from forgeos.core.context_assembly.assembler import ContextAssembler
from forgeos.core.context_assembly.models import ContextBundle, ContextItem, tier_for
from forgeos.core.graph import GraphStore, Node, NodeType
from forgeos.core.graph.store import Direction
from forgeos.core.memory import MemoryScope, MemoryService, MemoryStatus
from forgeos.core.token_intel.ledger import TokenLedger
from forgeos.ports.storage import StoragePort
from forgeos.ports.tokenizer import TokenizerPort

Clock = Callable[[], datetime.datetime]
_ADR_MAX_CHARS = 600


class AdvisoryContextBuilder:
    """Assemble grounding bundles for Mentor and Auditor from existing knowledge."""

    def __init__(
        self,
        graph: GraphStore,
        store: StoragePort,
        memory: MemoryService,
        tokenizer: TokenizerPort,
        ledger: TokenLedger | None = None,
        *,
        recent_limit: int = 5,
        clock: Clock = utcnow,
    ) -> None:
        self._graph = graph
        self._store = store
        self._memory = memory
        self._tokenizer = tokenizer
        self._ledger = ledger
        self._recent = recent_limit
        self._clock = clock
        self._order = 0

    # -- public entrypoints ----------------------------------------------------
    def for_mentor(
        self,
        focus: str,
        *,
        budget: int,
        depth: int = 2,
        adr_dir: Path | None = None,
        allow_source: bool = False,
        source_root: Path | None = None,
    ) -> ContextBundle:
        """Cards · Memory · ADRs · Repo Profile · Decisions · past Findings."""
        self._order = 0
        node = self._resolve(focus)
        reachable = self._reachable_subjects(node, depth)
        items: list[ContextItem] = []
        used_subject_memory: set[str] = set()
        items += self._subject_items(
            node, reachable, allow_source, source_root, used_subject_memory
        )
        items += self._decision_items(node, depth)
        items += self._finding_items(node, depth)
        items += self._adr_items(adr_dir)
        profile = self._repo_profile_item()
        if profile is not None:
            items.append(profile)
        items += self._memory_items(used_subject_memory)
        return self._assemble(node.id if node else focus, items, budget)

    def for_auditor(
        self,
        scope: str,
        *,
        budget: int,
        criteria: str = "",
        evidence: str = "",
        depth: int = 2,
    ) -> ContextBundle:
        """Acceptance Criteria · Decisions · past Findings · relevant Cards · Evidence."""
        self._order = 0
        node = self._resolve(scope)
        items: list[ContextItem] = []
        if criteria:
            items.append(self._text_item("criteria", "acceptance-criteria", criteria))
        if evidence:
            items.append(self._text_item("evidence", "available-evidence", evidence))
        reachable = self._reachable_subjects(node, depth)
        items += [
            i
            for i in self._subject_items(node, reachable, False, None, set())
            if i.kind == "card"
        ]
        items += self._decision_items(node, depth)
        items += self._finding_items(node, depth)
        return self._assemble(node.id if node else scope, items, budget)

    # -- assembly --------------------------------------------------------------
    def _assemble(self, scope_ref: str, items: list[ContextItem], budget: int) -> ContextBundle:
        assembler = ContextAssembler(
            self._graph, self._tokenizer, self._store, budget, self._ledger
        )
        return assembler.assemble(scope_ref, items)

    def _next_order(self) -> int:
        order = self._order
        self._order += 1
        return order

    def _item(
        self, kind: str, ref: str, content: str, raw_tokens: int | None = None
    ) -> ContextItem:
        tokens = self._tokenizer.count_text(content)
        return ContextItem(
            ref=ref, kind=kind, content=content, tokens=tokens,
            raw_tokens=raw_tokens if raw_tokens is not None else tokens,
            tier=tier_for(kind), order=self._next_order(),
        )

    def _text_item(self, kind: str, ref: str, text: str) -> ContextItem:
        return self._item(kind, ref, text)

    # -- sources ---------------------------------------------------------------
    def _resolve(self, focus: str) -> Node | None:
        return self._graph.get_node(focus) or self._graph.find_by_label(focus)

    def _reachable_subjects(self, node: Node | None, depth: int) -> list[Node]:
        if node is None:
            return []
        subjects = [
            n
            for n in self._graph.traverse(node.id, depth, direction=Direction.BOTH)
            if n.type in (NodeType.FILE, NodeType.MODULE)
        ]
        return subjects

    def _subject_items(
        self,
        node: Node | None,
        reachable: list[Node],
        allow_source: bool,
        source_root: Path | None,
        used_subject_memory: set[str],
    ) -> list[ContextItem]:
        subjects: list[Node] = []
        if node is not None and node.type in (NodeType.FILE, NodeType.MODULE):
            subjects.append(node)
        subjects += [n for n in reachable if n.id != (node.id if node else None)]

        items: list[ContextItem] = []
        for subject in subjects:
            items.append(
                self._best_subject_item(subject, allow_source, source_root, used_subject_memory)
            )
        return items

    def _best_subject_item(
        self,
        subject: Node,
        allow_source: bool,
        source_root: Path | None,
        used_subject_memory: set[str],
    ) -> ContextItem:
        # AC11 escalation: valid Card -> Memory -> Source -> stub.
        card = self._store.get(Collections.CARDS, card_id_for(subject.type.value, subject.id))
        if card is not None and self._card_valid(card, subject):
            raw_size = subject.props.get("size", 0)
            size = int(raw_size) if isinstance(raw_size, int | float | str) else 0
            content = str(card.get("purpose", ""))
            raw = max(self._tokenizer.count_text(content), (size + 3) // 4)
            return self._item("card", subject.id, content, raw)
        mem = self._subject_memory(subject.id)
        if mem is not None:
            used_subject_memory.add(mem)
            # Keep the subject's ref for lineage ("this subject, via memory").
            return self._item("memory", subject.id, self._memory_content(mem))
        if allow_source and subject.type == NodeType.FILE and source_root is not None:
            text = self._read_source(source_root, subject.label)
            return self._item("source", subject.id, text)
        return self._item("stub", subject.id, subject.label)

    @staticmethod
    def _card_valid(card: dict[str, object], subject: Node) -> bool:
        if subject.type != NodeType.FILE:
            return True
        return card.get("source_hash") == subject.props.get("hash")

    def _reachable_ids(self, node: Node | None, depth: int, node_type: NodeType) -> list[str]:
        if node is None:
            return []
        return [
            n.id
            for n in self._graph.traverse(
                node.id, depth, node_types=[node_type], direction=Direction.BOTH
            )
        ]

    def _recent_nodes(self, node_type: NodeType, exclude: set[str]) -> list[Node]:
        nodes = [n for n in self._graph.nodes(node_type) if n.id not in exclude]
        nodes.sort(key=lambda n: n.created_at, reverse=True)
        return nodes[: self._recent]

    def _decision_items(self, node: Node | None, depth: int) -> list[ContextItem]:
        items: list[ContextItem] = []
        seen: set[str] = set()
        for dec_id in self._reachable_ids(node, depth, NodeType.DECISION):  # reachable first
            dec = self._graph.get_node(dec_id)
            if dec is not None and dec_id not in seen:
                seen.add(dec_id)
                items.append(self._item("decision", dec_id, dec.label))
        for dec in self._recent_nodes(NodeType.DECISION, seen):  # recent-N fill
            seen.add(dec.id)
            items.append(self._item("decision", dec.id, dec.label))
        return items

    def _finding_items(self, node: Node | None, depth: int) -> list[ContextItem]:
        items: list[ContextItem] = []
        seen: set[str] = set()
        for fid in self._reachable_ids(node, depth, NodeType.AUDIT_FINDING):
            finding = self._graph.get_node(fid)
            if finding is not None and fid not in seen:
                seen.add(fid)
                items.append(self._item("finding", fid, self._finding_content(finding)))
        for finding in self._recent_nodes(NodeType.AUDIT_FINDING, seen):
            seen.add(finding.id)
            items.append(self._item("finding", finding.id, self._finding_content(finding)))
        return items

    @staticmethod
    def _finding_content(node: Node) -> str:
        rec = str(node.props.get("recommendation", "") or node.label)
        violations = node.props.get("violations", [])
        n = len(violations) if isinstance(violations, list) else 0
        return f"{node.label}: {rec} (violations: {n})"

    def _adr_items(self, adr_dir: Path | None) -> list[ContextItem]:
        if adr_dir is None or not adr_dir.is_dir():
            return []
        items: list[ContextItem] = []
        for path in sorted(adr_dir.glob("*.md")):
            full = path.read_text(encoding="utf-8", errors="replace")
            summary = self._adr_summary(full)
            items.append(
                self._item("adr", path.name, summary, raw_tokens=self._tokenizer.count_text(full))
            )
        return items

    @staticmethod
    def _adr_summary(text: str) -> str:
        marker = "## Decision"
        if marker in text:
            section = text.split(marker, 1)[1].split("\n##", 1)[0]
            return (marker + section).strip()[:_ADR_MAX_CHARS]
        return text.strip()[:_ADR_MAX_CHARS]

    def _repo_profile_item(self) -> ContextItem | None:
        profile = self._store.get(Collections.REPO_PROFILE, "profile")
        if not profile:
            return None
        langs = ",".join(profile.get("languages", []))
        content = (
            f"repo {profile.get('root', '')}: {profile.get('file_count', 0)} files, "
            f"{profile.get('module_count', 0)} modules; languages: {langs}"
        )
        return self._item("repo_profile", "repo_profile", content)

    def _memory_items(self, exclude: set[str]) -> list[ContextItem]:
        records = [
            r
            for scope in (MemoryScope.PROJECT, MemoryScope.USER)
            for r in self._memory.query(scope=scope, status=MemoryStatus.ACTIVE)
            if r.id not in exclude
        ]
        records.sort(key=lambda r: (r.salience, r.created_at), reverse=True)
        return [self._item("memory", r.id, r.content) for r in records[: self._recent]]

    def _subject_memory(self, node_id: str) -> str | None:
        for record in self._memory.query(status=MemoryStatus.ACTIVE):
            if node_id in record.links:
                return record.id
        return None

    def _memory_content(self, memory_id: str) -> str:
        record = self._memory.get(memory_id)
        return record.content if record is not None else memory_id

    @staticmethod
    def _read_source(source_root: Path, rel: str) -> str:
        try:
            return (source_root / rel).read_text(encoding="utf-8", errors="replace")[:8000]
        except OSError:
            return rel
