"""Execution Intelligence engine: scan Python sources into the symbol + call graph.

Deterministic and provider-free (ADR 0005/0015). E1 extracts Function/Method/Class
nodes + DEFINES/EXTENDS edges; E2 adds CALLS edges by resolving each call site against
the file's local defs, ``self`` methods, and import bindings (cross-file via a module
index). Calls it cannot resolve statically are counted, not emitted as dangling edges.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from forgeos.core.exec_intel.calls import RawCall, analyze_calls
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
    """Scan a repository's Python files into the execution symbol + call graph."""

    def __init__(self, store: ExecGraphStore) -> None:
        self._store = store

    def scan(self, root: Path) -> ExecScanResult:
        """Extract symbols and resolved calls from every Python file (idempotent)."""
        nodes: dict[str, ExecNode] = {}
        edges: dict[str, ExecEdge] = {}
        sources: dict[str, str] = {}
        for sf in iter_source_files(root):
            if sf.language != "python":
                continue
            source = (root / sf.path).read_text(encoding="utf-8", errors="replace")
            sources[sf.path] = source
            file_nodes, file_edges = extract_symbols(sf.path, source)
            for node in file_nodes:
                nodes[node.id] = node
            for edge in file_edges:
                edges[edge.id] = edge

        self._resolve_extends(nodes, edges)
        unresolved = self._resolve_calls(sources, nodes, edges)
        self._store.reconcile(nodes, edges)
        return _summarize(nodes, edges, len(sources), unresolved)

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
    def _resolve_calls(
        sources: dict[str, str],
        nodes: dict[str, ExecNode],
        edges: dict[str, ExecEdge],
    ) -> int:
        """Resolve call sites into CALLS edges; return the count left unresolved."""
        modindex = _module_index(sources.keys())
        unresolved = 0
        for file, source in sorted(sources.items()):
            imports, raw_calls = analyze_calls(file, source)
            for call in raw_calls:
                callee = _resolve_call(call, file, imports, modindex, nodes)
                if callee is None:
                    unresolved += 1
                    continue
                edge = ExecEdge(
                    id=f"{call.caller_id}|calls|{callee}",
                    src_id=call.caller_id,
                    dst_id=callee,
                    type=ExecEdgeType.CALLS,
                    confidence=Confidence.RESOLVED,
                )
                edges[edge.id] = edge
        return unresolved


def _module_index(paths: Iterable[str]) -> dict[str, str]:
    """Map dotted module name (repo-root-relative) -> file path."""
    index: dict[str, str] = {}
    for path in paths:
        if not path.endswith(".py"):
            continue
        mod = path[:-3].replace("/", ".")
        if mod.endswith(".__init__"):
            mod = mod[: -len(".__init__")]
        index[mod] = path
    return index


def _resolve_module(dotted: str, index: dict[str, str]) -> str | None:
    """Resolve a dotted module to a file: exact, else a unique path-suffix match."""
    if dotted in index:
        return index[dotted]
    parts = dotted.split(".")
    depth = len(parts)
    matches = sorted({f for m, f in index.items() if m.split(".")[-depth:] == parts})
    return matches[0] if len(matches) == 1 else None


def _candidate_in_file(file: str, symbol: str, nodes: dict[str, ExecNode]) -> str | None:
    for prefix in ("func", "class"):
        node_id = f"{prefix}:{file}#{symbol}"
        if node_id in nodes:
            return node_id
    return None


def _resolve_call(
    call: RawCall,
    file: str,
    imports: dict[str, tuple[str, str | None]],
    modindex: dict[str, str],
    nodes: dict[str, ExecNode],
) -> str | None:
    if call.via_self and call.cls is not None and call.attr is not None:
        node_id = f"func:{file}#{call.cls}.{call.attr}"
        return node_id if node_id in nodes else None
    if call.name is not None:
        return _name_target(call.name, file, imports, modindex, nodes)
    if call.base is not None and call.attr is not None:
        return _attr_target(call.base, call.attr, imports, modindex, nodes)
    return None


def _name_target(
    name: str,
    file: str,
    imports: dict[str, tuple[str, str | None]],
    modindex: dict[str, str],
    nodes: dict[str, ExecNode],
) -> str | None:
    local = _candidate_in_file(file, name, nodes)
    if local is not None:
        return local
    binding = imports.get(name)
    if binding is None:
        return None
    module, original = binding
    target_file = _resolve_module(module, modindex)
    if target_file is None:
        return None
    return _candidate_in_file(target_file, original if original is not None else name, nodes)


def _attr_target(
    base: str,
    attr: str,
    imports: dict[str, tuple[str, str | None]],
    modindex: dict[str, str],
    nodes: dict[str, ExecNode],
) -> str | None:
    binding = imports.get(base)
    if binding is None:
        return None
    module, original = binding
    target_file = _resolve_module(module, modindex)
    if target_file is None:
        return None
    if original is None:
        return _candidate_in_file(target_file, attr, nodes)
    node_id = f"func:{target_file}#{original}.{attr}"
    return node_id if node_id in nodes else None


def _summarize(
    nodes: dict[str, ExecNode],
    edges: dict[str, ExecEdge],
    file_count: int,
    unresolved_calls: int,
) -> ExecScanResult:
    return ExecScanResult(
        files=file_count,
        functions=sum(1 for n in nodes.values() if n.type is ExecNodeType.FUNCTION),
        methods=sum(1 for n in nodes.values() if n.type is ExecNodeType.METHOD),
        classes=sum(1 for n in nodes.values() if n.type is ExecNodeType.CLASS),
        defines_edges=sum(1 for e in edges.values() if e.type is ExecEdgeType.DEFINES),
        extends_edges=sum(1 for e in edges.values() if e.type is ExecEdgeType.EXTENDS),
        calls_edges=sum(1 for e in edges.values() if e.type is ExecEdgeType.CALLS),
        unresolved_calls=unresolved_calls,
    )
