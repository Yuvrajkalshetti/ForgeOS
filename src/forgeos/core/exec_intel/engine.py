"""Execution Intelligence engine: scan Python sources into the symbol graph (E1).

Deterministic and provider-free (ADR 0005/0015). Reuses RepoIntel's file walker, runs
the AST symbol extractor over every Python file, resolves class bases into EXTENDS
edges by name, and reconciles the result into the sibling ``ExecGraphStore`` — so a
re-scan is idempotent and drops symbols from deleted files.

Scope (E1): Function/Method/Class nodes, DEFINES edges, and name-matched EXTENDS edges.
CALLS, READS/WRITES, and OVERRIDES arrive in later phases (E2/E4).
"""

from __future__ import annotations

from pathlib import Path

from forgeos.core.exec_intel.models import (
    Confidence,
    ExecEdge,
    ExecEdgeType,
    ExecNode,
    ExecNodeType,
    ExecScanResult,
)
from forgeos.core.exec_intel.store import ExecGraphStore
from forgeos.core.exec_intel.symbols import extract_symbols
from forgeos.core.repo_intel.scanner import iter_source_files


class ExecIntelEngine:
    """Scan a repository's Python files into the execution symbol graph."""

    def __init__(self, store: ExecGraphStore) -> None:
        self._store = store

    def scan(self, root: Path) -> ExecScanResult:
        """Extract symbols from every Python file under ``root`` (idempotent)."""
        nodes: dict[str, ExecNode] = {}
        edges: dict[str, ExecEdge] = {}
        file_count = 0
        for sf in iter_source_files(root):
            if sf.language != "python":
                continue
            file_count += 1
            source = (root / sf.path).read_text(encoding="utf-8", errors="replace")
            file_nodes, file_edges = extract_symbols(sf.path, source)
            for node in file_nodes:
                nodes[node.id] = node
            for edge in file_edges:
                edges[edge.id] = edge

        self._resolve_extends(nodes, edges)
        self._store.reconcile(nodes, edges)
        return self._summarize(nodes, edges, file_count)

    @staticmethod
    def _resolve_extends(nodes: dict[str, ExecNode], edges: dict[str, ExecEdge]) -> None:
        """Add EXTENDS edges for class bases that match exactly one known class name."""
        by_name: dict[str, list[str]] = {}
        for node in nodes.values():
            if node.type is ExecNodeType.CLASS:
                simple = str(node.props.get("simple_name", node.label))
                by_name.setdefault(simple, []).append(node.id)
        for node in nodes.values():
            if node.type is not ExecNodeType.CLASS:
                continue
            raw_bases = node.props.get("bases")
            if not isinstance(raw_bases, list):
                continue
            for base in raw_bases:
                if not isinstance(base, str):
                    continue
                targets = by_name.get(base, [])
                if len(targets) == 1 and targets[0] != node.id:
                    edge = ExecEdge(
                        id=f"{node.id}|extends|{targets[0]}",
                        src_id=node.id,
                        dst_id=targets[0],
                        type=ExecEdgeType.EXTENDS,
                        confidence=Confidence.HEURISTIC,
                    )
                    edges[edge.id] = edge

    @staticmethod
    def _summarize(
        nodes: dict[str, ExecNode], edges: dict[str, ExecEdge], file_count: int
    ) -> ExecScanResult:
        return ExecScanResult(
            files=file_count,
            functions=sum(1 for n in nodes.values() if n.type is ExecNodeType.FUNCTION),
            methods=sum(1 for n in nodes.values() if n.type is ExecNodeType.METHOD),
            classes=sum(1 for n in nodes.values() if n.type is ExecNodeType.CLASS),
            defines_edges=sum(1 for e in edges.values() if e.type is ExecEdgeType.DEFINES),
            extends_edges=sum(1 for e in edges.values() if e.type is ExecEdgeType.EXTENDS),
        )
