# Phase Report — V1 Learning Workflow (human-gated review/approve/reject/commit)

- **Date:** 2026-06-21
- **Status:** ✅ build complete, gates green. STOP for human approval before next item.
- **Scope refs:** `docs/SCOPE-V1.md`, `docs/AMENDMENT-v1-scope.md` (ACs lines 110–118),
  ADR 0012. Highest-priority objective per the scope lock: the Knowledge → Learning →
  Skill loop.

## What was built
Core domain logic for the human-gated Learning pipeline. Previously `core/learning`
was emit/list only (`APPROVED` enum existed but nothing transitioned to it).

- **`core/learning/proposal.py`**
  - `ProposalStatus.COMMITTED` added (approved → committed = "Become a Skill").
  - `ProvenanceEntry` model (append-only audit record: action, actor, note,
    from_status, to_status, at).
  - `LearningProposal` gains `provenance: list[ProvenanceEntry]` and `skill_id: str|None`.
    (Additive, backward-compatible — no schema/`schema_version` change, per ADR 0008/0012.)
- **`core/learning/service.py`** — new `LearningService`:
  - `review()` — proposals awaiting decision (`proposed`), newest first.
  - `approve()` / `reject()` / `commit()` — explicit state machine; `actor` is
    **mandatory and keyword-only** (human-gated). Invalid transitions raise
    `InvalidTransition`; unknown id raises `KeyError`.
  - State machine: `proposed→approved`, `{proposed,approved}→rejected`,
    `approved→committed`. `rejected` and `committed` are terminal.
  - **`commit` performs "Become a Skill"**: creates a `NodeType.SKILL` graph node whose
    `props` carry lineage back to the proposal (`proposal_id`, `committed_by`,
    `committed_at`, `kind`, `evidence`, `reuse_value`); `proposal.skill_id` is set.
    Lineage is queryable both ways by id — **no new node/edge type** (reuses existing
    `NodeType.SKILL`, per AMENDMENT migration note).

## Acceptance criteria (AMENDMENT-v1-scope.md) — met
- ✅ review/approve/reject/commit transitions are human-only (actor required).
- ✅ no auto-promotion (emit yields `proposed`, empty provenance, no skill_id; nothing
  advances without an explicit `actor` call) — Principle 2 guard test.
- ✅ approval (and every transition) records provenance.
- ✅ commit creates a Skill node.
- ✅ full lineage queryable (proposal.skill_id ↔ skill.props["proposal_id"]).

## Tests (TDD)
`tests/unit/test_learning_workflow.py` — 11 tests (red → green): approve/reject
provenance, commit-requires-approval, commit-creates-skill-with-lineage, skill appears
in graph, approve-only-from-proposed, no-reject-after-commit, unknown-id, no
auto-promote, actor-required, review-pending-newest-first.

## Gates (verified on `$TMPDIR/forgeos`)
- `python3 scripts/check.py` → **OK (155 files)**.
- `pytest -p no:cacheprovider -W error::UserWarning` → **219 passed** (was 208; +11).
- Synced to `~/code/forgeos` and verified via Read tool.

## Architectural invariants honored
- Hexagonal: `core/learning` imports only `core/*` + `ports/*` (no adapters).
- Advisory↮learning isolation untouched (advisory still cannot import learning;
  existing boundary tests green).
- No schema change; additive only; deterministic transitions.

## Deliberately NOT in this increment (next steps)
- **CLI surface**: `forge learn review|approve|reject|commit` and `forge skill
  list|show`. The minimal-Skill *creation* half is done (commit → Skill node); the
  inspection CLI (`skill list|show`) and the `forge learn` command group remain.
- Portability CLI (export/import/backup), `forge init`, doc reconciliation.

## Note on scope coupling
The AMENDMENT couples "Learning commit" with "commit creates a Skill node," so this
increment delivers the commit→Skill-node creation (the heart of the loop) alongside the
Learning state machine. The remaining minimal-Skill work is the read-side CLI only.
