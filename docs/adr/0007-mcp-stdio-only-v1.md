# ADR 0007: MCP is supported but not required; stdio transport (deferred to V2 per ADR 0012)

- **Status:** accepted — **timing amended by ADR 0012 (MCP deferred to V2).**
- **Date:** 2026-06-20
- **Amended:** 2026-06-21 (ADR 0012) — MCP is **not** in V1. ForgeOS V1 is **CLI-first**.
  The stdio design below stands as the chosen transport **when MCP is built in V2**; the
  transport seam is preserved and no MCP code ships in V1.

## Context
Enterprise policy may block MCP; ForgeOS must function without it.

## Decision
ForgeOS exposes its own MCP server over **stdio only** (local Claude Code / Desktop),
as one transport adapter over the shared service layer; socket/HTTP is a later concern.
The CLI delivers full functionality if MCP is unavailable. **Per ADR 0012 the MCP adapter
itself is deferred to V2** (CLI-first V1); this ADR governs its design when implemented.

## Consequences
- No network-exposed surface in V1.
- CLI/MCP parity enforced by tests over the common service layer.
