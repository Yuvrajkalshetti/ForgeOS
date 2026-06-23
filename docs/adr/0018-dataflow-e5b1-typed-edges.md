# ADR 0018: Data Flow E5B.1 — typed (annotation/constructor) reads/writes

- **Status:** Accepted (E5B.1). Lineage + flow traversal (E5B.2) pending real TradeKit examples.
- **Date:** 2026-06-23
- **Extends:** ADR 0017.

## Context

E5A measured (count-only) how `recv.attr` accesses would resolve under a conservative TypeEnv.
The measurement showed where the receiver's type is known from declared annotations or a direct
constructor binding. E5B.1 turns those measured resolutions into actual graph edges so
cross-object state flow (e.g. `EntryEngine` writes `TradeState.stop_loss`) is queryable.

## Decision

1. Emit cross-object `READS`/`WRITES` edges when the receiver's type is known via the TypeEnv
   (parameter/local **annotation** or direct **constructor** binding). The edge targets
   `state:<typefile>#<Type>.<attr>`, where `<typefile>` is the receiver type's defining file,
   resolved by **unique class-name match** across the repo (deterministic; same mechanism as the
   exec graph's name resolution). Ambiguous or **externally-defined** types are **counted in the
   resolution stats but not edged** — never fabricate a target.
2. Every edge carries `resolution ∈ {self, annotation, constructor}` for provenance.
3. `self.<attr>` edges remain exact (`resolution=self`), as in E5A.
4. Report `typed_edges` (cross-object edges emitted) alongside the resolution stats.
5. Bounds unchanged: no SSA, symbolic execution, alias analysis, dynamic dispatch, or inference
   beyond the flow-insensitive TypeEnv.

## Consequences

- `forgeos_writers` / `forgeos_readers` / `forgeos_data_flow` / `forgeos_flow_impact` now
  surface cross-object state relationships (Signal→Execution-style facts), not just self-attr.
- Coverage is bounded by annotation/constructor density and by whether the type is a repo class.
- **Pending (E5B.2):** named lineage (LTP/MTM via anchors) and dedicated flow traversal — to be
  decided on real TradeKit resolution numbers before building.
