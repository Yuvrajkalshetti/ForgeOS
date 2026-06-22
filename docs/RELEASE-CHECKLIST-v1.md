# ForgeOS V1 Release Checklist

Two gates (per the approved V1 Scope Amendment / ADR 0012):
**Build Complete** = code+tests under standard gates; **Release Ready** = the items
below pass (mostly outside the sandbox).

## Gate A — V1 Build Complete (in-sandbox)
- [ ] Learning review/approve/reject/commit implemented; **no auto-promotion** (guard test); approval provenance recorded.
- [ ] Minimal Skill promotion: commit can create a `Skill` node; `forge skill list|show`; skills only via approved commit.
- [ ] Portability CLI: `forge export` → `forge import` round-trips; `forge backup` writes + prunes retention.
- [ ] `forge init` creates `.forgeos` (idempotent).
- [ ] Documentation reconciliation: Execution-agent names consistent (D1); MCP V1→V2 recorded (C1); Architecture V1 scope + roadmap updated.
- [ ] `python scripts/check.py` clean; `pytest -W error::UserWarning` green (no regressions).
- [ ] Architectural guards green: hexagonal (`core`↛`adapters`), provider-free engines (repo_intel/compression/context_assembly), advisory isolation (ADR 0010).

## Gate B — V1 Release Ready (real environment)
- [ ] **CI on a real toolchain:** `ruff check` clean, `mypy` (strict on `src/`) clean, `pytest` green (replaces the in-sandbox `scripts/check.py` substitute).
- [ ] **Live provider smoke:** one real Claude generate **and** one real Ollama generate each return text + usage; recorded by stats + ledger.
- [ ] **Real token reconciliation:** for a live call, provider-reported usage is stored as `tokens_actual`; `forge tokens report` shows estimate vs actual; reconciliation within tolerance (estimate is a reasonable predictor; actual is authoritative).
- [ ] **Portability on a real repo:** scan→compress→export→import round-trip reproduces graph+memory; backup/restore verified.
- [ ] **Determinism:** repeated scan/compress/context-build/agent-merge produce identical results.
- [ ] **Security:** no provider keys in snapshots or git; `.gitignore` excludes secrets + SQLite; import rejects path-traversal + newer schema.
- [ ] **Repo hygiene:** `git init` + initial commit (the standalone repo is not yet git-initialized — sandbox limitation); tag `v1.0.0`; CHANGELOG.
- [ ] **Docs:** README quickstart accurate; ADRs current; HANDOFF reflects V1 status.

## Notes
- Gate A is fully reproducible in the current sandbox. Gate B's live items require
  network + API key / local Ollama and a real Python toolchain (uv/ruff/mypy), so they
  run outside this environment.
- `forge install` is intentionally **not** a deliverable — install via `uv tool
  install forgeos` / pip (documented in README).
