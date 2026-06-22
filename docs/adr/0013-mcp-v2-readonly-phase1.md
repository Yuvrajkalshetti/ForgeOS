# ADR 0013 — MCP V2 Phase 1: read-only tools + mentor

- Status: Accepted
- Date: 2026-06-22
- Supersedes/extends: ADR 0007 (mcp-stdio-only-v1), ADR 0012 (v1-scope-decision)

## Context

V1 shipped CLI-first and froze the core; MCP was deferred to V2 (ADR 0007/0012).
The goal of this phase is the smallest safe MCP exposure so a Claude-connected
host can drive ForgeOS from chat, **without changing the frozen V1 core**.

An audit of the candidate tools found that the requested surface mixed read-only
and state-writing operations:

- Read-only: `status`, `doctor`, `skill list/show`, `graph query`, `memory query`.
- `scan` writes extensively (repo index + graph nodes/edges/profile).
- `mentor` writes advisory bookkeeping (a recommendation node, edges, an advisory
  session) **and** makes a live provider/LLM call.
- `memory gc` mutates (expire/decay) — so the read-only memory tool maps to
  `memory query`, not `gc`.

## Decision

Expose **seven** tools over a new stdio transport adapter
(`src/forgeos/adapters/transport/mcp/`) implementing `TransportPort`:

- Read-only (`readOnlyHint=true`): `forgeos_status`, `forgeos_doctor`,
  `forgeos_skill_list`, `forgeos_skill_show`, `forgeos_graph_summary`,
  `forgeos_memory_summary`.
- Action (`readOnlyHint=false`, `openWorldHint=true`): `forgeos_mentor` —
  explicitly annotated because it writes advisory records and calls the provider.

`scan`, `memory gc`, and all learning/export/import/backup/provider-config/install
operations are **out of scope** for this phase.

The adapter reuses the existing service layer and `open_store`/`provider_model`
helpers; it adds no business logic (CLI/MCP parity per ADR 0007). The `mcp` SDK is
an optional extra (`pip install forgeos[mcp]`); the `forge` CLI never imports it.

Note: opening the store runs idempotent SQLite migrations (`run_migrations`), so
the server needs write access to `<project>/.forgeos/cache/forge.sqlite`. This is
schema setup, not user-data mutation.

## Consequences

- New entrypoint `forgeos-mcp`; register it in a host's MCP config.
- Read-only invariant is enforced by tests (record counts unchanged before/after).
- CLI↔MCP parity is enforced by tests comparing JSON output.
- `mentor` cost/latency/secrets are the caller's concern; it fails gracefully
  (returns `{"error": ...}`) when no provider is configured.
- CI installs the `mcp` extra so the gates cover the adapter.
