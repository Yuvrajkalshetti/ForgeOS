# ADR 0019: Data Flow E5B.2 — anchored lineage + flow-path traversal

- **Status:** Accepted. Completes E5.
- **Date:** 2026-06-23
- **Extends:** ADR 0017/0018.

## Context

E5A/E5B.1 built the state graph (self + typed cross-object READS/WRITES). The headline
questions — "how does signal become execution?", "how does LTP become MTM?" — are *path*
queries that must cross both the call graph and the state graph, and reference domain concepts
(LTP, MTM) that are not code symbols.

## Decision

1. **Forward graph:** combine, into one directed adjacency, exec `CALLS` (caller -> callee),
   data `WRITES` (function -> state) and data `READS` (state -> reading function). Tracing
   "how does X reach Y" is then a **bounded path search** over it (deterministic; no SSA,
   symbolic execution, or inference).
2. **Anchors:** domain concepts map to symbols via `<project>/.forgeos/dataflow.yaml`
   (`anchors:` name -> symbol id/label) — the same human-declared pattern as ownership rules.
   The trading vocabulary lives in the project, not ForgeOS core.
3. **`forgeos_lineage(source, target)`** (read-only MCP tool): endpoints resolve via anchors,
   symbol ids, or labels; returns the bounded paths (or none — never a fabricated chain).

## Consequences

- Signal→Execution and (anchored) LTP→MTM are answerable to the extent the underlying CALLS
  and typed READS/WRITES edges exist (i.e. bounded by annotation/constructor resolution from
  E5B.1 and the call graph from E2). Gaps surface as "no path," never invented.
- E5 is complete. Remaining intelligence work (TS/JS, runtime tracing, full inference) stays
  out of scope per ADR 0015/0017.
