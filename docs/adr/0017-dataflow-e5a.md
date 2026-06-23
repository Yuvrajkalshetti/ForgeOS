# ADR 0017: Data Flow Intelligence — E5A self-attr reads/writes + resolution gate

- **Status:** Accepted (E5A). E5B (annotation/constructor-resolved cross-object edges) is
  **pending approval**, gated on measured resolution effectiveness.
- **Date:** 2026-06-23
- **Extends:** ADR 0015/0016.

## Context

The headline data-flow questions ("how does signal become execution?", "how does LTP become
MTM?", cross-class `TradeState.stop_loss` writers) require resolving the **type of the object**
behind `recv.attr`, which the v1 constraints (no type inference / SSA / symbolic exec / alias
analysis / dynamic dispatch) forbid. The v2 review proposed a conservative, annotation-driven
`TypeEnv` (self / parameter+local annotation / direct constructor) as the smallest unlock. The
go/no-go for that resolver (E5B) must be decided on **actual resolution effectiveness**, not
annotation density.

## Decision

**E5A (this ADR):**
1. **Emit** only `self.<attr>` `READS`/`WRITES` edges — the receiver type (enclosing class) is
   the one type known without inference. Stored in sibling `df_nodes`/`df_edges`. Class-attribute
   declarations become `StateSymbol` nodes. Deterministic, provider-free, idempotent.
2. **Measure** (count-only, **no edges emitted**) how every `recv.attr` access would resolve
   under the `TypeEnv` rules, reported as: `total_attribute_accesses`, `resolved_self`,
   `resolved_annotation`, `resolved_constructor`, `unresolved_accesses`, `resolution_rate`.
   The `TypeEnv` is flow-insensitive and conservative; nothing beyond it is attempted.
3. **Read-only MCP tools:** `forgeos_readers`, `forgeos_writers`, `forgeos_data_flow`,
   `forgeos_flow_impact` over the emitted self-attr graph (flow/impact reach into the E2/E3
   CALLS graph for transitive callers).
4. Cross-object accesses are **counted as unresolved, never edged.** No global tracking yet.

**E5B (pending):** if the measured `resolution_rate` on the target repo is high enough, wire the
annotation/constructor-resolved accesses into real cross-object `READS`/`WRITES` edges (enabling
Signal→Execution and, with anchors, LTP→MTM). Otherwise E5B is not worth building, and no
banned technique would change that.

## Consequences

- E5B is gated on a real effectiveness number, produced by E5A on the actual codebase.
- Strictly bounded: no SSA, symbolic execution, alias analysis, dynamic dispatch, or inference
  beyond the `TypeEnv`. Same input → same output.
- `forgeos_lineage` (named LTP/MTM) remains out until E5B + human anchors.
