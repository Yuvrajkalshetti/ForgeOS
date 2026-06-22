# Plan — V2 Execution Intelligence (E1–E5)

_Status: architecture approved (ADR 0015); implementation not started._

Execution Intelligence lets ForgeOS answer call-graph, impact, reachability, ownership, and
data-flow questions over a codebase. This plan is **Python-first**, deterministic, offline,
and provider-free (ADR 0005), built on the existing knowledge graph in **new collections**
(`exec_nodes`/`exec_edges`) via a new, isolated engine — no V1 refactor.

## Graph model (additive)

**Nodes** (`exec_nodes`): `Function` (`func:<file>#<qualname>`), `Method`
(`func:<file>#<Class>.<name>`), `Class` (`class:<file>#<qualname>`). `Interface` → `Class` +
`stereotype` prop. Entry points → `entrypoint` marker prop (`cli`/`fastapi_route`/`__main__`).

**Edges** (`exec_edges`, each with `confidence` + `resolution` props): `DEFINES`, `CALLS`,
`READS`, `WRITES`, `OVERRIDES`, `EXTENDS`, `OWNS{kind: derived|declared}`. Reverse direction
is derived via `traverse(direction=IN)` — not stored. New types require additive entries in
the graph edge registry.

## Static analysis approach (Python)

Two passes over `ast`: (1) build a symbol table (defs + bound imported names, stable qualname
ids); (2) resolve each `ast.Call` against local scope → module symbols → bound imports →
intra-class `self.method`. Tag `confidence`: module/imported/`self` calls → `resolved`;
unresolved receiver → `heuristic` (name-match) or `unresolved`. Incremental by file content
hash (reuse RepoIntel). Enforced provider-free via the import guard + `FailIfCalledProvider`.

## MCP tool surface (all read-only, provider-free; accept `project` + `min_confidence`)

| Tool | Query |
|---|---|
| `forgeos_who_calls` | reverse BFS over `CALLS` |
| `forgeos_call_graph` | forward BFS over `CALLS` |
| `forgeos_impact_analysis` | reverse reachability + touched files |
| `forgeos_paths_to` | bounded path search to a sink (“every path that places a live order”) |
| `forgeos_runtime_ownership` | derived + declared `OWNS`, labeled |
| `forgeos_data_flow` | structural trace between anchored endpoints |

## Phases

### E1 — Python Symbol Graph
- **Objective:** `Function`/`Method`/`Class` nodes + `DEFINES`/`OVERRIDES`/`EXTENDS` edges from
  Python AST; incremental by content hash.
- **Dependencies:** V1 graph + new collections.
- **Complexity:** Medium.
- **Acceptance:** every def/class → a stable-id node; idempotent re-scan (no dupes); JS/TS
  unchanged (import-level).
- **Tests:** golden-corpus symbol snapshot; import-guard; `FailIfCalledProvider`.
- **Risks:** qualname/scope edge cases (nested defs, decorators).

### E2 — Python Call Graph
- **Objective:** `CALLS` edges with `confidence`/`resolution`; bind imported names.
- **Dependencies:** E1.
- **Complexity:** High (resolution is the hard part).
- **Acceptance:** validated `resolved`-tier precision on the golden corpus; unresolved calls
  recorded (not dropped); deterministic across runs.
- **Tests:** curated corpus with known edges → precision/recall on the `resolved` tier;
  determinism check.
- **Risks:** false edges — the core risk; gate by confidence.

### E3 — Impact & Path Queries + MCP
- **Objective:** `who_calls`, `call_graph`, `impact_analysis`, `paths_to` MCP tools.
- **Dependencies:** E2.
- **Complexity:** Low–Medium (traversal + tool wiring; reuses the read-only MCP pattern).
- **Acceptance:** correct results filtered by `min_confidence`; read-only invariant holds.
- **Tests:** MCP tool tests + CLI parity; read-only invariant (no writes).
- **Risks:** path blow-up → bound depth/results.

### E4 — State & Ownership
- **Objective:** `StateSymbol` nodes, `READS`/`WRITES`, derived `OWNS`; declared `OWNS` via the
  learning loop; `forgeos_runtime_ownership`.
- **Dependencies:** E1 (E2 helps).
- **Complexity:** Medium.
- **Acceptance:** derived owner matches majority-writer on corpus; declared ownership flows
  through review; both labeled distinctly; contested ownership flagged (not silently picked).
- **Tests:** corpus ownership cases.
- **Risks:** attribute aliasing → mark heuristic.

### E5 — Structural Data Flow
- **Objective:** return/arg propagation views + anchored named-flow tracing; `forgeos_data_flow`.
- **Dependencies:** E2, E4.
- **Complexity:** High; lowest fidelity.
- **Acceptance:** structural trace between two anchored endpoints is correct and deterministic;
  semantics come only from anchors.
- **Tests:** corpus flow cases between known endpoints.
- **Risks:** over-promising auto-discovery — scoped to structural + anchored.

## Out of scope (separate, separately-approved tracks)

- TS/JS symbol & call graph (needs a TypeScript toolchain; would leave the “offline/pure-Python”
  envelope) — so cross-language flows (e.g. Python backend ↔ Next.js UI) are **not** covered.
- Dynamic / runtime execution tracing (requires running the code).

## Two decisions to confirm before E1

1. Separate-collections approach (`exec_nodes`/`exec_edges`): parameterize `GraphStore`'s
   collections, or add a sibling `ExecGraphStore`?
2. Accept Python-only scope for now, with the TS/Next.js side explicitly deferred.

## Recommendation

Sequence **E1 → E3 first** — symbols → calls → impact/path queries deliver ~80% of the value
(“who calls this”, “what breaks”, “every path to a live order”) at the lowest risk. Schedule
E4–E5 (ownership, data flow) after E3 proves the substrate scales.
