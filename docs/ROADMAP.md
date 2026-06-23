# ForgeOS — Roadmap & Status

_Last updated: 2026-06-23_

An honest snapshot of what's shipped, in progress, and deferred. Decisions live in `docs/adr/`.

## V1 — shipped (v1.0.0)

- ✅ Knowledge OS, Memory, Knowledge Graph, Context Assembly, Learning (human-gated), Skills
  (minimal; full graph deferred — ADR 0012), Mentor, Auditor, CLI (`forge`/`forgeos`), Usability.

> ⚠️ Provider adapters are unit-tested; the live LLM round-trip is post-release validation
> (not run). Not exercised by the Claude Code / MCP workflow (no provider needed there).

## V2 — MCP (shipped, read-only, no provider — the host model reasons)

- Knowledge: `forgeos_status`, `forgeos_doctor`, `forgeos_skill_list`, `forgeos_skill_show`,
  `forgeos_graph_summary`, `forgeos_memory_summary`, `forgeos_advisory_context` (ADR 0007/0013/0014).
- Execution: `forgeos_symbol`, `forgeos_call_graph`, `forgeos_impact_analysis`, `forgeos_paths_to` (ADR 0015).
- Ownership: `forgeos_runtime_owner`, `forgeos_runtime_summary` (ADR 0016).
- Data flow: `forgeos_readers`, `forgeos_writers`, `forgeos_data_flow`, `forgeos_flow_impact` (ADR 0017).

Claude Code verified live; Claude Desktop documented (not yet verified end-to-end).

## V2 — Execution / Ownership / Data-Flow Intelligence

Python-first, deterministic/offline/provider-free, on the existing graph via isolated engines
(`core/exec_intel`, `core/ownership_intel`, `core/dataflow_intel`). Run with **`forge exec-scan`**.

- ✅ **E1** symbol graph · ✅ **E2** call graph · ✅ **E3** impact/path MCP tools · ✅ **E4** declared+observed ownership (ADR 0016).
- ✅ **E5A** — self-attribute READS/WRITES + **count-only resolution measurement** (self /
  annotation / constructor / unresolved + rate) reported by `exec-scan` (ADR 0017).
- 🔄 **E5B** — annotation/constructor-resolved cross-object edges (Signal→Execution; LTP→MTM
  with anchors). **Gated on the measured resolution rate on the target repo.**

> Out of scope: TS/JS, type inference beyond TypeEnv, SSA, symbolic execution, alias analysis,
> dynamic dispatch, runtime tracing — so cross-language flows are not covered.

## Future — not approved

- ⏳ Full Skill Graph (ADR 0012) · Dashboard · Voice · Organization Layer · Vector retrieval
  (`VectorPort` unwired, ADR 0003).
