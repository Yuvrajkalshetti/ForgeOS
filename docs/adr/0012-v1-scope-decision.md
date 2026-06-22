# ADR 0012: V1 scope decision — defer MCP and full Skill Graph to V2

- **Status:** accepted (2026-06-21)
- **Date:** 2026-06-21
- **Refs:** ADR 0007 (MCP stdio-only), `docs/AMENDMENT-v1-scope.md`
- **Note:** Approved with a two-tier model — **V1 Build Complete** (code+tests) vs
  **V1 Release Ready** (live smoke + real token reconciliation + release checklist).

## Context
The Architecture lists "MCP Adapter" and "Skill Graph" in V1 scope, but also states
ForgeOS "does not require MCP" (CLI is sufficient), and skills only arise from approved
learning (which is not yet built). Building MCP + a full Skill Graph now risks
significant effort that does not contribute to the first usable release.

## Decision
- **Defer the MCP stdio adapter + CLI↔MCP parity to V2.** Keep the transport seam.
- **Keep only a minimal Skill capability in V1** (Skill nodes created via approved
  Learning commit; `forge skill list|show`); **defer the full Skill Graph service**
  (lifecycle/versioning/search/invocation) to V2.
- V1 completion = current P0–P6.6 + human-gated Learning commit (with minimal Skill
  promotion) + portability CLI + `forge init` + documentation reconciliation +
  live-provider smoke. `forge install` is removed (installation is not a feature).

See `docs/AMENDMENT-v1-scope.md` for full V1/V2 scope, rationale, migration impact,
and acceptance-criteria changes.

## Consequences
- Shortest credible path to a usable, CLI-complete V1 centered on token efficiency.
- Additive, reversible deferrals (seams + `Skill` node type already exist); no schema
  change; existing 208 tests unaffected.
- Requires stakeholder acceptance of deferring two originally-listed V1 items.
