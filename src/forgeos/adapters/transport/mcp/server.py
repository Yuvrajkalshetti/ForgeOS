"""ForgeOS MCP stdio transport (V2).

Thin transport adapter (ADR 0007): adapts MCP to the same services the CLI uses, no business
logic. All tools are **read-only** (``readOnlyHint=True``) and need **no LLM provider** — the
host (Claude) reasons. Knowledge tools wrap V1; execution/ownership/data-flow tools query the
Intelligence graphs (ADR 0015/0016/0017).

stdout carries only the MCP protocol; logging goes to stderr.
"""

from __future__ import annotations

import dataclasses
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from forgeos.adapters.tokenizer import LocalEstimator
from forgeos.adapters.transport.cli._shared import open_store
from forgeos.catalog import Collections
from forgeos.config.loader import load_config
from forgeos.core.advisory import AdvisoryContextBuilder
from forgeos.core.dataflow_intel import DataFlowStore, query as df_query
from forgeos.core.exec_intel import ExecGraphStore
from forgeos.core.exec_intel.models import Confidence
from forgeos.core.exec_intel.query import callees, callers, impact, paths_to, resolve
from forgeos.core.graph import GraphStore, NodeType
from forgeos.core.memory import MemoryKind, MemoryScope, MemoryService
from forgeos.core.ownership_intel import classify, load_rules, runtime_summary
from forgeos.observability import configure_logging, new_request_id

_FORGEOS_DIR = ".forgeos"
_READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
_CONF_BY_NAME: dict[str, Confidence] = {c.value: c for c in Confidence}

mcp_app = FastMCP("forgeos")


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_status(project: str = ".") -> dict[str, Any]:
    """Summarize what ForgeOS knows about a project and the active provider."""
    root = Path(project)
    store = open_store(root)
    graph = GraphStore(store)
    counts = {
        "memory": len(store.query(Collections.MEMORY)),
        "nodes": len(store.query(Collections.NODES)),
        "edges": len(store.query(Collections.EDGES)),
        "cards": len(store.query(Collections.CARDS)),
        "skills": len(graph.nodes(NodeType.SKILL)),
        "proposals": len(store.query(Collections.PROPOSALS)),
        "advisory_sessions": len(store.query(Collections.ADVISORY_SESSIONS)),
    }
    return {
        "project": str(root),
        "initialized": (root / _FORGEOS_DIR).exists(),
        "provider": load_config(project_dir=root).providers.default,
        "counts": counts,
    }


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_doctor(project: str = ".") -> dict[str, Any]:
    """Diagnose ForgeOS setup for a project. Read-only; never calls a provider."""
    root = Path(project)
    checks: list[dict[str, str]] = []

    def check(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    if (root / _FORGEOS_DIR).exists():
        check("initialized", "OK", f"{root / _FORGEOS_DIR} present")
        try:
            open_store(root)
            check("store", "OK", "snapshot store opens; index rebuildable")
        except Exception as exc:  # diagnostic must not raise
            check("store", "FAIL", f"cannot open store: {exc}")
    else:
        check("initialized", "FAIL", "project not initialized — run `forgeos init`")

    config = load_config(project_dir=root)
    default = config.providers.default
    check("provider", "OK", f"default provider: {default}")
    if default == "claude":
        env = config.providers.claude.api_key_env
        if os.environ.get(env):
            check("credentials", "OK", f"${env} is set")
        else:
            check("credentials", "FAIL", f"${env} not set — `export {env}=...` to use Claude")
    elif default == "ollama":
        check("credentials", "INFO", f"ollama needs no key; host {config.providers.ollama.host}")
    else:
        check("credentials", "INFO", f"provider '{default}' — verify its setup")

    py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    check("python", "OK" if sys.version_info >= (3, 12) else "FAIL", f"Python {py} (need >=3.12)")

    return {"ok": not any(c["status"] == "FAIL" for c in checks), "checks": checks}


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_skill_list(project: str = ".") -> list[dict[str, Any]]:
    """List all Skill nodes created by approved learning commits."""
    graph = GraphStore(open_store(Path(project)))
    return [s.model_dump(mode="json") for s in graph.nodes(NodeType.SKILL)]


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_skill_show(target: str, project: str = ".") -> dict[str, Any]:
    """Show one Skill node by id or label."""
    graph = GraphStore(open_store(Path(project)))
    node = graph.get_node(target) or graph.find_by_label(target)
    if node is None or node.type is not NodeType.SKILL:
        return {"error": f"skill not found: {target}"}
    return node.model_dump(mode="json")


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_graph_summary(
    target: str, depth: int = 2, project: str = "."
) -> dict[str, Any]:
    """Traverse the knowledge graph from a node (id or label); return reachable nodes."""
    graph = GraphStore(open_store(Path(project)))
    node_id: str | None = target if graph.get_node(target) is not None else None
    if node_id is None:
        found = graph.find_by_label(target)
        node_id = found.id if found is not None else None
    if node_id is None:
        return {"error": f"node not found: {target}"}
    reachable = graph.traverse(node_id, max_depth=depth)
    return {"start": node_id, "nodes": [n.model_dump(mode="json") for n in reachable]}


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_memory_summary(
    scope: MemoryScope | None = None,
    kind: MemoryKind | None = None,
    project: str = ".",
) -> list[dict[str, Any]]:
    """Return memory records (newest first), optionally filtered by scope/kind."""
    service = MemoryService(open_store(Path(project)))
    records = service.query(scope=scope, kind=kind)
    return [r.model_dump(mode="json") for r in records]


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_advisory_context(
    focus: str,
    depth: int = 2,
    budget: int | None = None,
    project: str = ".",
) -> dict[str, Any]:
    """Assemble Mentor's provider-free grounding bundle for a focus node or topic.

    Returns the deterministic ``ContextBundle`` ``forge mentor`` would feed an LLM — cards,
    memory, ADRs, repo profile, decisions, findings — so the host model reasons itself.
    Read-only: built with no token ledger, so nothing is persisted (ADR 0014).
    """
    root = Path(project)
    store = open_store(root)
    config = load_config(project_dir=root)
    builder = AdvisoryContextBuilder(
        GraphStore(store), store, MemoryService(store), LocalEstimator()
    )
    adr = root / "docs" / "adr"
    bundle = builder.for_mentor(
        focus,
        budget=budget if budget is not None else (config.tokens.per_request or 8000),
        depth=depth,
        adr_dir=adr if adr.is_dir() else None,
        allow_source=False,
        source_root=root,
    )
    return bundle.model_dump(mode="json")


def _exec_confidence(value: str) -> Confidence:
    return _CONF_BY_NAME.get(value, Confidence.RESOLVED)


def _brief(store: ExecGraphStore, node_id: str) -> dict[str, Any]:
    node = store.get_node(node_id)
    if node is None:
        return {"id": node_id}
    return {"id": node.id, "type": node.type.value, "label": node.label, "file": node.file}


def _resolve_target(
    store: ExecGraphStore, target: str
) -> tuple[str | None, dict[str, Any] | None]:
    ids = resolve(store, target)
    if not ids:
        return None, {"error": f"symbol not found: {target}"}
    if len(ids) > 1:
        return None, {"error": f"ambiguous symbol: {target}", "candidates": ids[:25]}
    return ids[0], None


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_symbol(query: str, project: str = ".") -> list[dict[str, Any]]:
    """Find code symbols (function/method/class) whose qualname contains ``query``."""
    store = ExecGraphStore(open_store(Path(project)))
    matches = [n for n in store.nodes() if query in n.label]
    return [_brief(store, n.id) for n in matches[:50]]


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_call_graph(
    target: str,
    direction: str = "callees",
    depth: int = 2,
    min_confidence: str = "resolved",
    project: str = ".",
) -> dict[str, Any]:
    """Callers or callees of a symbol over the CALLS graph (direction: callers|callees)."""
    store = ExecGraphStore(open_store(Path(project)))
    node_id, err = _resolve_target(store, target)
    if node_id is None:
        return err if err is not None else {"error": "unresolved"}
    conf = _exec_confidence(min_confidence)
    found = (
        callers(store, node_id, depth, conf)
        if direction == "callers"
        else callees(store, node_id, depth, conf)
    )
    return {
        "target": node_id,
        "direction": direction,
        "symbols": [_brief(store, i) for i in found],
    }


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_impact_analysis(
    target: str, min_confidence: str = "resolved", project: str = "."
) -> dict[str, Any]:
    """Transitive callers of a symbol (what may break if it changes) + the files touched."""
    store = ExecGraphStore(open_store(Path(project)))
    node_id, err = _resolve_target(store, target)
    if node_id is None:
        return err if err is not None else {"error": "unresolved"}
    upstream = impact(store, node_id, _exec_confidence(min_confidence))
    dependents = [_brief(store, i) for i in upstream]
    files = sorted({b["file"] for b in dependents if "file" in b})
    return {"target": node_id, "dependents": dependents, "files": files}


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_paths_to(
    target: str,
    max_depth: int = 6,
    max_paths: int = 20,
    min_confidence: str = "resolved",
    project: str = ".",
) -> dict[str, Any]:
    """Call paths that reach a target symbol (e.g. every path that reaches a sink)."""
    store = ExecGraphStore(open_store(Path(project)))
    node_id, err = _resolve_target(store, target)
    if node_id is None:
        return err if err is not None else {"error": "unresolved"}
    chains = paths_to(store, node_id, max_depth, max_paths, _exec_confidence(min_confidence))
    return {"target": node_id, "paths": [[_brief(store, i) for i in chain] for chain in chains]}


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_runtime_owner(symbol: str, project: str = ".") -> dict[str, Any]:
    """Declared + observed ownership of a symbol (domain/layer/criticality/impact, ADR 0016)."""
    root = Path(project)
    store = ExecGraphStore(open_store(root))
    node_id, err = _resolve_target(store, symbol)
    if node_id is None:
        return err if err is not None else {"error": "unresolved"}
    return dataclasses.asdict(classify(store, node_id, load_rules(root)))


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_runtime_summary(symbol: str, project: str = ".") -> dict[str, Any]:
    """Ownership + consumers + dependencies + governance labels for a symbol."""
    root = Path(project)
    store = ExecGraphStore(open_store(root))
    node_id, err = _resolve_target(store, symbol)
    if node_id is None:
        return err if err is not None else {"error": "unresolved"}
    return runtime_summary(store, node_id, load_rules(root))


def _resolve_state(
    df: DataFlowStore, symbol: str
) -> tuple[str | None, dict[str, Any] | None]:
    ids = df_query.resolve(df, symbol)
    if not ids:
        return None, {"error": f"state symbol not found: {symbol}"}
    if len(ids) > 1:
        return None, {"error": f"ambiguous state symbol: {symbol}", "candidates": ids[:25]}
    return ids[0], None


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_writers(symbol: str, project: str = ".") -> dict[str, Any]:
    """Functions/methods that write a state symbol (``<Class>.<attr>``)."""
    store = open_store(Path(project))
    df = DataFlowStore(store)
    state_id, err = _resolve_state(df, symbol)
    if state_id is None:
        return err if err is not None else {"error": "unresolved"}
    exec_store = ExecGraphStore(store)
    found = [_brief(exec_store, w) for w in df_query.writers(df, state_id)]
    return {"symbol": state_id, "writers": found}


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_readers(symbol: str, project: str = ".") -> dict[str, Any]:
    """Functions/methods that read a state symbol (``<Class>.<attr>``)."""
    store = open_store(Path(project))
    df = DataFlowStore(store)
    state_id, err = _resolve_state(df, symbol)
    if state_id is None:
        return err if err is not None else {"error": "unresolved"}
    exec_store = ExecGraphStore(store)
    found = [_brief(exec_store, r) for r in df_query.readers(df, state_id)]
    return {"symbol": state_id, "readers": found}


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_data_flow(symbol: str, project: str = ".") -> dict[str, Any]:
    """Upstream/downstream of a state symbol (writers/readers + their callers)."""
    store = open_store(Path(project))
    df = DataFlowStore(store)
    state_id, err = _resolve_state(df, symbol)
    if state_id is None:
        return err if err is not None else {"error": "unresolved"}
    exec_store = ExecGraphStore(store)
    flow = df_query.data_flow(df, exec_store, state_id)
    return {
        "symbol": state_id,
        "upstream": [_brief(exec_store, i) for i in flow["upstream"]],
        "downstream": [_brief(exec_store, i) for i in flow["downstream"]],
    }


@mcp_app.tool(annotations=_READ_ONLY)
async def forgeos_flow_impact(symbol: str, project: str = ".") -> dict[str, Any]:
    """All symbols affected by a state symbol: readers/writers + their transitive callers."""
    store = open_store(Path(project))
    df = DataFlowStore(store)
    state_id, err = _resolve_state(df, symbol)
    if state_id is None:
        return err if err is not None else {"error": "unresolved"}
    exec_store = ExecGraphStore(store)
    affected = df_query.flow_impact(df, exec_store, state_id)
    return {"symbol": state_id, "affected_symbols": [_brief(exec_store, i) for i in affected]}


class MCPTransport:
    """``TransportPort`` implementation that serves the MCP stdio loop."""

    name = "mcp"

    def run(self) -> None:
        """Serve the FastMCP app over stdio (stdout = protocol, stderr = logs)."""
        mcp_app.run()


def main() -> None:
    """Console-script entrypoint (``forgeos-mcp``)."""
    configure_logging()
    new_request_id()
    MCPTransport().run()


if __name__ == "__main__":
    main()
