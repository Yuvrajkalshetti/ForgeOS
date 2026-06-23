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
> but the **live LLM round-trip** (real generate + token reconciliation) is **post-release
> validation** and has not been run. It is **not exercised by the Claude Code / MCP workflow**,
> which requires no provider — so this only matters for the provider-backed `forge mentor`
> / `audit` CLI commands.

## V2 — MCP (shipped)

- ✅ **MCP Integration.** Read-only stdio tools, no provider required (the host model reasons):
  - Knowledge: `forgeos_status`, `forgeos_doctor`, `forgeos_skill_list`, `forgeos_skill_show`,
    `forgeos_graph_summary`, `forgeos_memory_summary`, `forgeos_advisory_context` (ADR 0007/0013/0014).
  - Execution Intelligence (E3): `forgeos_symbol`, `forgeos_call_graph`, `forgeos_impact_analysis`,
    `forgeos_paths_to` (ADR 0015), defaulting to `min_confidence=resolved`.
- ✅ **Claude Code integration** — verified live.
- 🔄 **Claude Desktop integration** — documented (config in the README); not yet verified end-to-end.

## V2 — Execution Intelligence (in progress)

Design in **ADR 0015**; phased plan in `docs/PLAN-V2-execution-intelligence.md`. Python-first,
deterministic/offline/provider-free, built on the existing graph via a new isolated engine
(`core/exec_intel`) + sibling collections. Run extraction with **`forge exec-scan`**.

- ✅ **E1** — Python symbol graph: `Function`/`Method`/`Class` + `DEFINES` + name-matched `EXTENDS`.
- ✅ **E2** — Python call graph: `CALLS` edges (same-file / `self` / imported, cross-file via a
  module index), confidence-tagged; unresolved calls counted, not edged.
- ✅ **E3** — impact & path queries as read-only MCP tools (`forgeos_symbol`, `forgeos_call_graph`,
  `forgeos_impact_analysis`, `forgeos_paths_to`), default `min_confidence=resolved`.
- 🔄 **E4** — state & ownership (`READS`/`WRITES`, derived + declared `OWNS`)
- 🔄 **E5** — structural data flow (anchored)

> Scope note: Python-first. TS/JS call graphs, type inference, dynamic/runtime tracing, ownership,
> and data flow are **out of scope** for E1–E3 (E4/E5 or separate, separately-approved tracks) —
> so cross-language flows through the Next.js UI are not covered.

## Future — not approved

Out of scope until explicitly approved:

- ⏳ Full Skill Graph (lifecycle / versioning / search / invocation) — deferred per ADR 0012
- ⏳ Dashboard
- ⏳ Voice
- ⏳ Organization Layer
- ⏳ Vector / embedding retrieval — `VectorPort` seam exists but is unwired (ADR 0003)
