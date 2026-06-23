# ForgeOS — Roadmap & Status

_Last updated: 2026-06-23_

An honest snapshot of what's shipped, in progress, and deferred. The decisions behind each
item live in `docs/adr/`.

## V1 — shipped (v1.0.0)

All components are built and unit-tested:

- ✅ **Knowledge OS**, **Memory**, **Knowledge Graph**, **Context Assembly**, **Learning**
  (propose → review → approve → commit), **Skills** (minimal; full Skill Graph deferred, ADR 0012),
  **Mentor**, **Auditor**, **CLI** (`forge`/`forgeos`), **Usability layer** (`init`/`doctor`/`status`/`wizard`).

> ⚠️ **Caveat:** the Claude/Ollama **provider adapters** are unit-tested, but the **live LLM
> round-trip** is **post-release validation** (not run). Not exercised by the Claude Code / MCP
> workflow, which needs no provider — only the provider-backed `forge mentor` / `audit` CLI.

## V2 — MCP (shipped)

Read-only stdio tools, no provider required (the host model reasons):

- Knowledge: `forgeos_status`, `forgeos_doctor`, `forgeos_skill_list`, `forgeos_skill_show`,
  `forgeos_graph_summary`, `forgeos_memory_summary`, `forgeos_advisory_context` (ADR 0007/0013/0014).
- Execution Intelligence: `forgeos_symbol`, `forgeos_call_graph`, `forgeos_impact_analysis`,
  `forgeos_paths_to` (ADR 0015).
- Ownership Intelligence: `forgeos_runtime_owner`, `forgeos_runtime_summary` (ADR 0016).

Claude Code integration verified live; Claude Desktop documented (not yet verified end-to-end).

## V2 — Execution + Ownership Intelligence

Design in **ADR 0015 / 0016**; plan in `docs/PLAN-V2-execution-intelligence.md`. Python-first,
deterministic/offline/provider-free, on the existing graph via isolated engines
(`core/exec_intel`, `core/ownership_intel`) + sibling collections. Run extraction with
**`forge exec-scan`**.

- ✅ **E1** — Python symbol graph (`Function`/`Method`/`Class` + `DEFINES` + name-matched `EXTENDS`).
- ✅ **E2** — Python call graph (`CALLS`, confidence-tagged; unresolved counted, not edged).
- ✅ **E3** — impact & path query MCP tools (default `min_confidence=resolved`).
- ✅ **E4** — declared + observed ownership (rules + call-graph), drift detection; criticality /
  impact remain rule-only governance metadata (ADR 0016).
- 🔄 **E5** — structural data flow (anchored).

> Scope: Python-first. TS/JS call graphs, type inference, dynamic/runtime tracing, mutation
> tracking, and data flow are **out of scope** for E1–E4 (E5 or separate tracks) — so
> cross-language flows through the Next.js UI are not covered.

## Future — not approved

- ⏳ Full Skill Graph (ADR 0012) · Dashboard · Voice · Organization Layer · Vector/embedding
  retrieval (`VectorPort` seam unwired, ADR 0003).
