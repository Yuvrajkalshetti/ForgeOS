# ADR 0002: SQLite as rebuildable index, YAML/JSON snapshots as source of truth

- **Status:** accepted
- **Date:** 2026-06-20

## Context
Knowledge must be portable, diffable, and survive runtime loss; queries must be
fast and dependency-light.

## Decision
YAML/JSON snapshots committed to git are the canonical source of truth. SQLite is
a derived, rebuildable query index. On conflict or corruption, rebuild SQLite from
snapshots.

## Alternatives considered
- Embedded graph DB (Kùzu/DuckDB) — extra dependency, weaker portability.
- Plain files only — slow queries, hand-rolled traversal.

## Consequences
- `forge export`/`import` rebuild SQLite anywhere; backups are snapshot bundles.
- Write-through sync (SQLite + queued snapshot) must stay consistent (tested).
