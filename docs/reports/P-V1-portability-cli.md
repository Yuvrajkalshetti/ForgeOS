# Implementation Report — V1 Portability CLI + `forge init`

- **Date:** 2026-06-21 · **Status:** ✅ build complete, gates green, STOP for approval.
- **Scope refs:** approved increment "Portability CLI + forge init"; `docs/SCOPE-V1.md`,
  `docs/AMENDMENT-v1-scope.md` (V1 item 4), ADR 0008 (generic store / rebuildable index).

## Executive Summary
Wired the existing, tested `services/portability.py` functions to the CLI and added an
idempotent `forge init`. Pure transport wiring — **no portability service behavior was
modified**, no new storage/graph/provider/abstraction introduced. The Knowledge →
Learning → Skill artifacts (and all knowledge) are now portable from the command line:
`forge export`, `forge import`, `forge backup`, and `forge init`.

## Files Added
- `src/forgeos/adapters/transport/cli/portability.py` — `export_cmd`, `import_cmd`,
  `backup_cmd`, `init_cmd`.
- `tests/unit/test_portability_cli.py` — 8 tests.

## Files Modified
- `src/forgeos/adapters/transport/cli/app.py` — import + register `export`/`import`/
  `backup`/`init` as top-level commands.

## Architecture Compliance Review
- **No service change:** commands call `export_bundle` / `import_bundle` /
  `backup` unmodified. Defect search found none, so nothing was touched.
- **Snapshots = source of truth (ADR 0008):** import restores YAML, then the store is
  re-opened so the SQLite index is rebuilt from snapshots (`SnapshotStore.open` →
  `rebuild_index`). No SQLite is ever shipped in a bundle.
- **Hexagonal:** logic stays in `services/` (core-side) + `adapters/transport/cli`
  (transport). No new abstractions; CLI/MCP parity preserved (same service layer a V2
  MCP transport would use).
- **No new node/edge/provider types; no schema/`schema_version` change.**
- Constraints honored: did not revisit MCP, Skill Graph scope, or V1 scope.

## Acceptance Criteria Review
- ✅ `forge export <dest>` — exposes export; writes bundle; prints path.
- ✅ `forge import <bundle>` — exposes import; restores snapshots; rebuilds index;
  prints manifest. Invalid/missing bundle → exit 1; newer schema_version → exit 1.
- ✅ `forge backup [--retention N]` — timestamped bundle + prune to retention.
- ✅ `forge init` — initializes `<project>/.forgeos` layout; **idempotent**, safe to
  re-run, **does not overwrite existing data** (re-open rebuilds index from existing
  snapshots without deleting them); reports `created: true|false`.

## Tests Added (`tests/unit/test_portability_cli.py`, TDD red→green)
1. export creates bundle
2. import restores records (round-trip A→B, queryable after import)
3. import bad/missing bundle → exit 1
4. import rejects newer schema_version → exit 1
5. backup creates + prunes to retention (5 runs, retention 3 → 3 remain)
6. init creates project structure (`created: true`)
7. init idempotent + preserves data (`created: false`, seeded record intact)
8. full CLI round-trip: init A → seed → export → init B → import → verify

## Risks
- **Low.** Backup filenames use microsecond timestamps; rapid successive backups in the
  same microsecond could theoretically collide — mirrors the pre-existing service test
  (`for _ in range(5)`) which passes; not observed.
- `forge import` merges into existing snapshots (does not clear first) — matches the
  service's documented behavior; an import over a populated project overlays records.
  Out of scope to change (no service-behavior changes authorized).

## Deviations From Plan
- None. Scope delivered exactly as approved; no service redesign.

## Tests / Gates
- `scripts/check.py` → OK (160 files). `pytest -W error::UserWarning` → **235 passed**
  (227 → 235, +8). All previous tests incl. the 4 `test_portability.py` service tests
  remain green. Synced to `~/code/forgeos`, verified via Read tool.

## Confidence Assessment
**High.** Thin wiring over already-tested services; deterministic; round-trip and
idempotency verified end-to-end through the CLI; full suite green.

## Remaining V1 build surface (NOT started)
- Documentation reconciliation (execution-agent naming D1; MCP V1→V2 scope C1).
- Release gates (separate from build): live Claude/Ollama smoke · token reconciliation ·
  release checklist.
