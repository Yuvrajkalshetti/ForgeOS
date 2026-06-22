# ADR 0008: Generic record store backs StoragePort; typed tables/indexes roll out per engine

- **Status:** accepted
- **Date:** 2026-06-20

## Context
`StoragePort` (P0) is a generic collection/record interface: `put(collection,
id, data)` over plain mappings, with typed domain models layered on top by the
core engines. The Implementation Plan §5 also specifies concrete physical tables
(`nodes`, `edges`, `memory`, `token_events`, `provider_stats`, `cards`,
`proposals`) with entity-specific indexes (e.g. `idx_edges_src`).

P1's exit criterion is the **export/import round-trip** and snapshot↔SQLite
consistency — not query performance, which only matters once the graph engine
(P3) and memory queries (P2) exist.

## Decision
P1 implements SQLite as a single generic, rebuildable `records(collection, id,
data_json, updated_at)` table satisfying `StoragePort`. The logical collections
from §5 are addressed by name (see `forgeos.catalog`). Entity-specific physical
tables and performance indexes (notably edge traversal indexes) are introduced
**by the consuming phase** via the migration runner (P2 memory, P3 graph), when
real query patterns exist.

YAML snapshots remain the source of truth; SQLite (whatever its physical shape)
remains a rebuildable index. This decision changes neither the storage strategy
nor the knowledge model — only the sequencing of physical schema rollout.

## Alternatives considered
- Build all typed tables + indexes now — premature without domain models (P2/P3)
  and against "prefer simple"; indexes would guard queries that don't yet exist.
- Per-collection tables now — more schema churn for no P1 benefit.

## Consequences
- P1 stays small and the round-trip is provable today.
- Migrations are forward-only and additive; later phases add typed tables/indexes
  without reworking the port or the snapshot format.
- Generic `query` filters in Python for now; replaced by indexed SQL where a phase
  needs it (tracked as technical debt until P3).
