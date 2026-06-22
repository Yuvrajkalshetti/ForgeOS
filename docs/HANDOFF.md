# ForgeOS — Continuation / Handoff Brief

> Purpose: everything a fresh (post-compaction or post-restart) session needs to
> continue ForgeOS without re-deriving context. Read this first.

## What ForgeOS is
Local-first AI Operating System: memory, knowledge graph, deterministic context
compression, context assembly, token intelligence, providers + orchestrator, and an
Advisory System. Goal: preserve knowledge while sending fewer tokens.

Authoritative design docs (in this repo):
- **`docs/SCOPE-V1.md` (V1 scope LOCKED, 2026-06-21 — read this; it governs what's in/out of V1)**
- `docs/ARCHITECTURE.md` (Rev 3), `docs/IMPLEMENTATION_PLAN.md`
- `docs/AMENDMENT-advisory-system.md`, `docs/AUDIT-mcp-skill.md`, `docs/RELEASE-CHECKLIST-v1.md`, `docs/adr/0001..0010`

## Phase status (as of v1.0.0 release-prep, 2026-06-22)
- ✅ P0 Foundation · P1 Storage/Portability · P2 Memory+Lifecycle · P3 Knowledge Graph
  · P4 RepoIntel (provider-free) · P5 Token/Compression/Assembly · P6 Providers+Orchestrator
  · P6.5 Advisory System (Mentor+Auditor)
  · **P6.6 Advisory Intelligence Wiring — DONE** (`AdvisoryContextBuilder` composes
    Cards/Memory/KG/RepoProfile/ADRs/Decisions/past-Findings into a budgeted ContextBundle;
    Mentor/Auditor consume `grounding` + record `grounding_refs`; wired into `forge mentor`/
    `forge audit`. Verified: 34 advisory tests green, full suite 208.)
- ✅ **Learning workflow core — DONE** (2026-06-21; `docs/reports/P-V1-learning-workflow.md`):
  `LearningService.review/approve/reject/commit` (human-gated, `actor` mandatory, full
  provenance, no auto-promote); `commit` "Becomes a Skill" → creates a `NodeType.SKILL`
  node with lineage in props. +11 tests.
- ✅ **Learning/Skill CLI — DONE** (2026-06-21; `docs/reports/P-V1-learning-skill-cli.md`):
  `forge learn review|approve|reject|commit` (`--actor` required) + `forge skill list|show`.
  Loop usable end-to-end from CLI. +8 tests.
- ✅ **Portability CLI + `forge init` — DONE** (2026-06-21; `docs/reports/P-V1-portability-cli.md`):
  `forge export|import|backup|init` wired over existing `services/portability.py` (no service
  change). `init` idempotent + non-destructive. +8 tests.
- ✅ **Documentation reconciliation — DONE** (2026-06-21; `docs/reports/P-V1-doc-reconciliation.md`):
  D1 execution-agent naming unified to **Architect/Engineer/QA/Reviewer/Security**; C1 MCP
  **V1→V2** + full Skill Graph→V2 / minimal Skill→V1 applied across ARCHITECTURE, IMPLEMENTATION_PLAN,
  ADR 0007, advisory amendment. No code/test changes.
- ✅ **V1.1 usability layer — DONE** (2026-06-22; `docs/reports/P-V1.1-usability.md`):
  `forgeos doctor` · `forgeos status` · `forgeos` console alias (kept `forge`) · `init`
  next-steps guidance · `forgeos wizard`. Thin UX only; no core change. +7 tests.
- ✅ **One-line installer — DONE** (2026-06-22): `install.sh` / `install.ps1`
  (`uv tool install --force .` + `uv tool update-shell` → global `forgeos`/`forge`). +2 tests.
- ✅ **Lint/type cleanup — DONE** (2026-06-22): ruff config (`per-file-ignores` for tests;
  ignore `UP042`/`PLR2004`) + production line-wraps; 8 mypy-strict errors fixed. See RELEASE STATUS.
- ⏳ **Remaining V1 work = release mechanics only** (see `docs/RELEASE-CHECKLIST-v1.md`):
  confirm README quickstart accuracy · write `CHANGELOG.md` · `git init` + commit + tag `v1.0.0`.
  - **Deferred to V2:** MCP stdio transport + CLI↔MCP parity; full Skill Graph
    (lifecycle/versioning/deprecation/search/invocation/governance).
  - **Documented known limitation (providers unavailable in this env):** real Claude smoke,
    real Ollama smoke, token reconciliation → post-release validation, NOT v1.0.0 blockers.
- Tests: **244 passing**. Workflow: per-phase TDD → gates → report → STOP for human approval.

## RELEASE STATUS — v1.0.0 (2026-06-22): BUILD COMPLETE · conditional GO
**All gates GREEN on the real toolchain** (run by the human on their Mac, not the sandbox):
`uv run ruff check .` → All checks passed · `uv run mypy` → Success (98 files) ·
`uv run pytest -W error::UserWarning` → **244 passed**. (In-sandbox substitute
`python3 scripts/check.py` → OK.)
- ✅ Mandatory blockers cleared: CI toolchain green; secrets/`.gitignore` verified (keys
  env-only; `*.sqlite` + secret patterns git-ignored; import rejects path-traversal + newer schema).
- ⏳ Before tagging `v1.0.0`: confirm README quickstart · add `CHANGELOG.md` · `git tag v1.0.0`.
- Release-notes known limitation: live Claude/Ollama smoke + token reconciliation are
  **unverified** (providers unavailable here) → validate post-release. V1 is **CLI-first / local-first**.

## ~~Known open gap~~ — RESOLVED in P6.6 (2026-06-21)
The brief originally flagged advisory as "intelligence-blind." That gap is **closed**:
`core/advisory/context.py::AdvisoryContextBuilder` wires Memory, Knowledge Graph,
RepoProfile, Cards, Context Assembly, ADRs, and past AuditFindings into a deterministic,
budgeted `ContextBundle` (provider-free); `Mentor.advise`/`Auditor.audit` consume it via
`grounding=` and persist `grounding_refs` for lineage; `forge mentor`/`forge audit` build
and pass it on the real call path. Evidence: `test_advisory_context.py`,
`test_advisory_grounding.py`, `test_p6_6_cli.py` (34 advisory tests green; suite 208).
The dev tree was already ahead of this brief when P6.6 was built.

## ENVIRONMENT WORKAROUNDS (critical — non-standard)
- **Toolchain:** `uv`, `ruff`, `mypy` are NOT installed and CANNOT be installed
  (PyPI/network blocked; only `fictiv.atlassian.net` allowed). `pytest` IS installed.
  `git` is unavailable in-sandbox.
- **Gates per phase** (substitute for ruff/mypy, which are real in CI via `.github/workflows/ci.yml`):
  - Lint/type substitute: `python3 scripts/check.py` (stdlib syntax + annotation + import hygiene; mirrors ruff F401/`__all__`/`__future__`).
  - Tests: `PYTHONNOUSERSITE=1 python3 -m pytest -p no:cacheprovider -W error::UserWarning`
- **Filesystem sandbox quirks:**
  - Bash CANNOT read `~/code` or `~/Documents/...` (read-denied). Bash CAN *write* `~/code`.
  - Bash has full read+write only in `$TMPDIR` (e.g. `/tmp/claude-XXX`).
  - The Read/Write/Edit tools CAN read+write `~/code` (they bypass the bash sandbox).
- **Workspace model:**
  - **Durable source of truth:** `~/code/forgeos` (this repo). `docs/ARCHITECTURE.md`,
    `docs/IMPLEMENTATION_PLAN.md`, `docs/HANDOFF.md`, `docs/SCOPE-V1.md` live ONLY here.
  - **⚠️ As of 2026-06-22, `~/code/forgeos` is AHEAD of any `$TMPDIR` copy and is canonical.**
    The human ran `uv run ruff check . --fix` there (import-sorting in `cli/app.py` + 5 test
    files; a yoda-condition flip in `test_card_generator.py`). **Do NOT `cp -R $TMPDIR → ~/code`**
    — that would clobber those fixes. If you need a dev tree, copy the OTHER way:
    `cp -R ~/code/forgeos "$TMPDIR/forgeos"`, then run gates there.
  - The old "sync `$TMPDIR → ~/code` after a green phase" rule is **suspended** — only valid when
    `$TMPDIR` is the newer tree, which it is not now.

## Rehydration
- **Canonical tree is `~/code/forgeos`** and it is GREEN on the human's real `uv` toolchain.
  No code work is pending — only release mechanics (README/CHANGELOG/git tag).
- **If a dev tree is needed for gates:** the human copies `cp -R ~/code/forgeos "$TMPDIR/forgeos"`
  and tells Claude the path. Never copy `$TMPDIR → ~/code` (see Workspace warning above).
- **Real gates run on the human's machine** (`uv run ruff check . && uv run mypy && uv run
  pytest -W error::UserWarning`); the in-sandbox substitute is `python3 scripts/check.py` + pytest.

## Available libs (importable in sandbox)
pydantic v2, PyYAML, typer, click, httpx, jsonschema, rich, tomllib (stdlib). Missing:
`anthropic` (use httpx; Claude adapter already does), `ulid` (stdlib `_ids.py` used).

## Architectural invariants (do not break)
- Hexagonal: `core/` never imports `adapters/` (guard test).
- Provider-free (no LLM, no provider import): `core/repo_intel`, `core/compression`,
  `core/context_assembly` (ADR 0005, 0009; guard tests).
- Advisory ↮ Execution isolation; advisory cannot execute/deploy/merge/approve or mutate
  learning state (ADR 0010; boundary tests).
- YAML snapshots = source of truth; SQLite = rebuildable index (ADR 0008).
- Learning is human-approved only; nothing auto-promotes.
- Deterministic: RepoIntel, Compression, Context Assembly, orchestrator merge.

## Resume prompt to paste in a new session
"Resume ForgeOS. Read docs/HANDOFF.md and docs/SCOPE-V1.md in ~/code/forgeos first.
State: V1 is BUILD COMPLETE and all gates are GREEN on my real toolchain
(uv run ruff check . = passed; uv run mypy = success/98 files; uv run pytest
-W error::UserWarning = 244 passed). V1 core + V1.1 are FROZEN — no feature,
architecture, refactor, MCP, provider, or Skill-Graph work.

Only release mechanics remain for v1.0.0: (1) confirm README quickstart matches the
real CLI, (2) write CHANGELOG.md, (3) git init + commit + tag v1.0.0. Live Claude/
Ollama smoke + token reconciliation are a DOCUMENTED KNOWN LIMITATION (providers
unavailable here) — post-release validation, not blockers.

Workspace: ~/code/forgeos is canonical and AHEAD of any $TMPDIR copy (I ran
`ruff --fix` there) — do NOT cp -R $TMPDIR over ~/code. Edit durable files in ~/code
directly. git is unavailable in your sandbox; I run git/tag commands on my Mac.
Don't implement anything; help me cut the v1.0.0 release. Await my go."
