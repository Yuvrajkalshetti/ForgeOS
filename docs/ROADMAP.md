# ForgeOS — Roadmap & Status

_Last updated: 2026-06-23_

An honest snapshot of what's shipped, in progress, and deferred. The decisions behind each
item live in `docs/adr/`.

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

## V2 — MCP (shipped)

- ✅ **MCP Integration — Phase 1.** Seven **read-only** stdio tools: `forgeos_status`,
  `forgeos_doctor`, `forgeos_skill_list`, `forgeos_skill_show`, `forgeos_graph_summary`,
  `forgeos_memory_summary`, `forgeos_advisory_context`. No provider required — the host model
  (Claude) does the reasoning (ADR 0007, 0013, 0014). CI-verified and tested live in Claude Code.
- ✅ **Claude Code integration** — verified live.
- 🔄 **Claude Desktop integration** — documented (config in the README); not yet verified end-to-end.
- 🔄 **Broader MCP (write / action tools)** — deliberately deferred; the MCP surface is read-only by design.

> The former provider-calling `forgeos_mentor` MCP tool was **replaced** by
> `forgeos_advisory_context` (read-only grounding; the host model reasons) — see ADR 0014.
> The provider-backed `forge mentor` CLI command is unchanged.

## V2 — Execution Intelligence (in progress)

Design in **ADR 0015**; phased plan in `docs/PLAN-V2-execution-intelligence.md`. Python-first,
deterministic/offline/provider-free, built on the existing graph via a new isolated engine
(`core/exec_intel`) + sibling collections.

- ✅ **E1** — Python symbol graph: `Function`/`Method`/`Class` nodes + `DEFINES` edges +
  name-matched `EXTENDS` (confidence=heuristic). Run it with **`forge exec-scan`**. (`OVERRIDES` → E2.)
- 🔄 **E2** — Python call graph (`CALLS`, confidence-tagged) via an import-binding resolver
- 🔄 **E3** — impact & path queries + read-only MCP tools (`who_calls`, `call_graph`, `impact_analysis`, `paths_to`)
- 🔄 **E4** — state & ownership (`READS`/`WRITES`, derived + declared `OWNS`)
- 🔄 **E5** — structural data flow (anchored)

> Scope note: Python-first. TS/JS call graphs and dynamic/runtime tracing are **out of scope**
> for E1–E5 (separate, heavier, separately-approved tracks) — so cross-language flows through
> the Next.js UI are not covered.

## Future — not approved

Out of scope until explicitly approved:

- ⏳ Full Skill Graph (lifecycle / versioning / search / invocation) — deferred per ADR 0012
- ⏳ Dashboard
- ⏳ Voice
- ⏳ Organization Layer
- ⏳ Vector / embedding retrieval — `VectorPort` seam exists but is unwired (ADR 0003)
