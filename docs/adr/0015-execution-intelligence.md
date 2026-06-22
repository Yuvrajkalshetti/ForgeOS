# ADR 0015: Execution Intelligence — shared graph, isolated engine, Python-first

- **Status:** Accepted (architecture). Implementation is phased (E1–E5) and **not started**.
- **Date:** 2026-06-22
- **Builds on:** ADR 0003 (graph-first retrieval), ADR 0005 (RepoIntel deterministic & provider-free), ADR 0008 (generic record store)

## Context

ForgeOS should answer execution-level questions: call graph (“who calls X?”), impact
(“what breaks if I change X?”), reachability (“every path that can place a live order”),
state ownership, and data flow. Today the knowledge graph is **file/module-granular** with
**import-only** edges (RepoIntel emits `File`/`Module`/`Dependency` nodes and
`contains`/`depends_on` edges). There are no `Function`/`Class` nodes and no call edges.

## Decision

1. **Same graph, new engine, new collections.** Execution Intelligence reuses the existing
   knowledge graph so execution facts cross-link with `Decision`/`Skill`/memory/`AuditFinding`
   — this cross-linking is the reason the capability belongs in ForgeOS rather than a
   standalone tool. It is built as a **separate engine** writing to **new collections**
   (`exec_nodes`, `exec_edges`), **not** merged into the lightweight `forgeos scan` path nor
   into the V1 `nodes.yaml`/`edges.yaml` snapshots. Additive only (parameterize the graph
   store's target collections, or add a sibling store) — **no V1 refactor, no V1 behavior change**.
2. **Python-first.** Symbol/call extraction targets Python via the stdlib `ast` — consistent
   with ADR 0005 (deterministic, offline, provider-free). TS/JS remain import-level as today.
   A TS symbol/call engine (TypeScript compiler API / tree-sitter) is a **separate, heavier,
   separately-approved** track. **Dynamic/runtime tracing is out of scope** (it would require
   executing the code — violating offline + determinism).
3. **Node types (additive):** `Function`, `Method`, `Class`. `Interface` is **rejected** (Python
   has none — use `Class` + a `stereotype` prop for ABC/Protocol); `EntryPoint` is a **marker
   prop**, not a node type.
4. **Edge types (additive, registry-validated):** `CALLS`, `DEFINES`, `READS`, `WRITES`,
   `OVERRIDES`, `EXTENDS`, `OWNS`. `CALLED_BY` is **rejected** — derive the reverse via
   `traverse(direction=IN)`; storing both directions doubles the edge count (the worst scale
   lever). A node-level `RETURNS` edge is **rejected** — encode return-use as a prop / in the
   data-flow view.
5. **Confidence is mandatory.** Every exec edge carries `confidence ∈ {exact, resolved,
   heuristic, unresolved}`. Static Python call resolution is undecidable in general; approximate
   call edges must never be indistinguishable from exact import edges. MCP tools and queries
   default to `resolved`+.
6. **Ownership and data flow are split into mechanical + human layers.** *Derived* ownership =
   the component holding the majority of `WRITES` to a state symbol; *declared* ownership = a
   human assertion captured via the existing learning loop. Data flow = auto-derived
   **structural** propagation (over `CALLS` + `READS`/`WRITES`) plus **human-anchored** named
   flows — not pure semantic auto-discovery (a static engine cannot know a variable “is LTP”).

## Consequences

- Execution queries compose with existing knowledge (e.g., “decisions governing the functions
  that reach `place_order`”).
- New **read-only, provider-free** MCP tools become possible (`who_calls`, `call_graph`,
  `impact_analysis`, `paths_to`, `runtime_ownership`, `data_flow`) — same contract as the
  shipped MCP set.
- **Scale is the primary risk:** symbol granularity is ~10–30× file granularity. Mitigated by
  separate collections (protect V1 snapshots), SQLite indexes on `exec_edges` endpoints,
  content-hash incremental re-extraction (reusing RepoIntel's pattern), and not storing
  reverse edges or materialized paths.
- TS/Next.js code is **not** call-analyzable under this ADR; cross-language flow is not promised.
- Implementation is sequenced **E1→E5** (see `docs/PLAN-V2-execution-intelligence.md`); E1–E3
  deliver most of the value at the lowest risk.
