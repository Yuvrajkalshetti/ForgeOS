# ForgeOS — Roadmap & Status

_Last updated: 2026-06-22_

An honest snapshot of what's shipped, in progress, and deferred. The decisions behind
each item live in `docs/adr/`.

## V1 — shipped (v1.0.0)

All components are built and unit-tested:

- ✅ **Knowledge OS** — the overall local-first system
- ✅ **Memory** (`core/memory`)
- ✅ **Knowledge Graph** (`core/graph`)
- ✅ **Context Assembly** (`core/context_assembly`)
- ✅ **Learning** — human-gated loop: propose → review → approve → commit (`core/learning`)
- ✅ **Skills** — minimal (list / show); the full Skill Graph is deferred (ADR 0012)
- ✅ **Mentor** (`core/advisory/mentor.py`)
- ✅ **Auditor** (`core/advisory/auditor.py`)
- ✅ **CLI** (`forge` / `forgeos`)
- ✅ **Usability layer** (`init`, `doctor`, `status`, `wizard`)

> ⚠️ **Caveat:** the Claude/Ollama **provider adapters** are implemented and unit-tested,
> but the **live LLM round-trip** (real generate + token reconciliation against
> provider-reported usage) is **post-release validation** and has not been run. It is
> **not exercised by the Claude Code / MCP workflow**, which requires no provider — so this
> only matters for the provider-backed `forge mentor` / `audit` CLI commands.

## V2 — in progress

- ✅ **MCP Integration — Phase 1 shipped.** Seven **read-only** stdio tools: `forgeos_status`,
  `forgeos_doctor`, `forgeos_skill_list`, `forgeos_skill_show`, `forgeos_graph_summary`,
  `forgeos_memory_summary`, `forgeos_advisory_context`. No provider required — the host model
  (Claude) does the reasoning (ADR 0007, 0013, 0014). CI-verified and tested live in Claude Code.
- ✅ **Claude Code integration** — verified live.
- 🔄 **Claude Desktop integration** — documented (config provided in the README); not yet
  verified end-to-end.
- 🔄 **Broader MCP (write / action tools)** — deliberately deferred; the MCP surface is
  read-only by design.

> The former provider-calling `forgeos_mentor` MCP tool was **replaced** by
> `forgeos_advisory_context` (read-only grounding; the host model reasons) — see ADR 0014.
> The provider-backed `forge mentor` CLI command is unchanged.

## Future — not approved

Out of scope until explicitly approved:

- ⏳ Execution Intelligence
- ⏳ Call Graphs
- ⏳ Runtime Ownership
- ⏳ Data Flow Analysis
- ⏳ Full Skill Graph (lifecycle / versioning / search / invocation) — deferred per ADR 0012
- ⏳ Dashboard
- ⏳ Voice
- ⏳ Organization Layer
