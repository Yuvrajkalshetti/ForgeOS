"""ForgeOS MCP transport adapter (V2 Phase 1).

A stdio MCP server that exposes existing ForgeOS services as tools. Imported only
when the ``forgeos-mcp`` entrypoint runs (or in tests); the ``forge`` CLI never
imports it, so the optional ``mcp`` dependency stays optional.
"""

from __future__ import annotations

from forgeos.adapters.transport.mcp.server import MCPTransport, main, mcp_app

__all__ = ["MCPTransport", "main", "mcp_app"]
