"""ForgeOS MCP stdio transport (V2 Phase 1).

Exposes existing ForgeOS services as MCP tools so a Claude host (Claude Code /
Claude Desktop) can drive ForgeOS from chat. Per ADR 0007 this is a thin transport
adapter: it adapts the MCP protocol to the same services the CLI uses and contains
no business logic, which is what preserves CLI/MCP parity.

All seven tools are **read-only** (``readOnlyHint=True``) and require **no LLM
provider** — in the MCP model the host (Claude Code) is the reasoning model. In
particular ``forgeos_advisory_context`` returns Mentor's provider-free grounding
bundle (built with no token ledger, so nothing is persisted) for the host to reason
over, instead of ForgeOS making its own provider call (ADR 0014).

stdout carries only the MCP protocol; logging is configured to stderr
(:func:`forgeos.observability.configure_logging`), keeping the channel clean.
"""

from __future__ import annotations

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
from forgeos.core.graph import GraphStore, NodeType
from forgeos.core.memory import MemoryKind, MemoryScope, MemoryService
from forgeos.observability import configure_logging, new_request_id

_FORGEOS_DIR = ".forgeos"
_READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)

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

    Returns the same deterministic ``ContextBundle`` that ``forge mentor`` would feed
    to an LLM — cards, memory, ADRs, repo profile, decisions, findings — so the host
    model (Claude Code) can do the reasoning itself. Read-only: built with no token
    ledger, so nothing is persisted (ADR 0014).
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
