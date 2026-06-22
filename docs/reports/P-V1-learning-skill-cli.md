# Phase Report — V1 Learning/Skill CLI surface (`forge learn` + `forge skill`)

- **Date:** 2026-06-21
- **Status:** ✅ build complete, gates green. STOP for human approval before next item.
- **Scope refs:** `docs/SCOPE-V1.md`, `docs/AMENDMENT-v1-scope.md` (V1 items 2–3), ADR 0012.
  Completes the **read/drive surface** for the Knowledge → Learning → Skill loop.

## What was built
The CLI surface over the `LearningService` (built in the prior increment) plus minimal
Skill inspection. End-to-end, the loop is now usable from the command line.

- **`adapters/transport/cli/learn.py`** — `forge learn` group:
  - `review` — list proposals awaiting a decision (newest first).
  - `approve` / `reject` / `commit` — `--actor` is **required** (recorded in provenance),
    `--note` optional. `commit` "Becomes a Skill". `KeyError`→exit 1 (not found);
    `InvalidTransition`→exit 1 (with message).
- **`adapters/transport/cli/skill.py`** — `forge skill` group:
  - `list` — all Skill nodes as JSON.
  - `show <id|label>` — one Skill node incl. lineage in `props`; exit 1 if not found.
- **`app.py`** — registered `learn_app` (`learn`) and `skill_app` (`skill`).

## Acceptance criteria — met
- ✅ `forge skill list|show` (minimal Skill capability; no lifecycle/versioning/search/
  invocation — those remain V2).
- ✅ Skills exist **only** via approved commit (creation lives in `LearningService.commit`;
  the CLI exposes no skill-creation path).
- ✅ Human-gated transitions surfaced with mandatory `--actor`.

## Tests (TDD)
`tests/unit/test_learning_cli.py` — 8 tests (red → green): review-lists-pending,
approve-records-provenance(+no-longer-pending), reject, commit→skill→`skill list`/`skill
show` lineage, commit-without-approval-fails, approve-unknown-id-fails, skill-list-empty,
skill-show-unknown-fails.

## Gates (verified on `$TMPDIR/forgeos`)
- `python3 scripts/check.py` → **OK (158 files)**.
- `pytest -p no:cacheprovider -W error::UserWarning` → **227 passed** (was 219; +8).
- Synced to `~/code/forgeos` and verified via Read tool.

## Architectural invariants honored
- CLI lives in `adapters/transport/cli` (transport seam); reuses the same service/store
  layer an MCP transport would use later (CLI/MCP parity preserved for V2).
- No new node/edge types; deterministic; no schema change.

## Remaining V1 build surface
- Portability CLI: `forge export` / `import` / `backup` (services exist in
  `services/portability.py`; wire to CLI).
- `forge init`.
- Documentation reconciliation (execution-agent naming D1; MCP scope C1).
- Release gates (separate): live Claude/Ollama smoke · token reconciliation · checklist.
