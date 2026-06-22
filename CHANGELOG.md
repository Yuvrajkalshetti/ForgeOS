# Changelog

All notable changes to ForgeOS are documented here. This project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html) and the spirit of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] — 2026-06-22

First public release. ForgeOS V1 is **CLI-first** and **local-first**: it preserves
knowledge while sending fewer tokens, with human-controlled learning throughout.

### Added

**Core platform (P0–P6.6)**
- Foundation: layered configuration, structured logging with request correlation,
  hexagonal ports/adapters seam (`core/` never imports `adapters/`, enforced by guard tests).
- Storage & portability: YAML snapshots as the source of truth with a rebuildable SQLite
  index (ADR 0008).
- Memory + lifecycle: add/query/gc with retention.
- Knowledge graph: typed nodes/edges with query and edge-explanation (`why`).
- RepoIntel: deterministic, provider-free repository scanning into memory + graph.
- Token intelligence, deterministic context compression, and budgeted context assembly
  (provider-free; ADR 0005, 0009).
- Providers + orchestrator: Claude (httpx) and Ollama adapters behind a provider port,
  with a deterministic merge.
- Advisory System (P6.5–P6.6): Mentor + Auditor grounded by an `AdvisoryContextBuilder`
  that composes Cards/Memory/KG/RepoProfile/ADRs/Decisions/past-Findings into a budgeted
  `ContextBundle`; advisory records `grounding_refs` for lineage. Advisory is isolated from
  execution — it cannot execute, deploy, merge, approve, or mutate learning state (ADR 0010).

**Human-gated learning loop**
- `LearningService` review / approve / reject / commit — every transition requires an
  `--actor` and records full provenance. **Nothing auto-promotes.**
- Minimal Skill promotion: an approved proposal's `commit` "Becomes a Skill" — creates a
  Skill graph node with lineage in its props.
- CLI: `forge learn review|approve|reject|commit` and `forge skill list|show`.

**Portability & workspace**
- `forge export` / `import` / `backup` (with retention pruning) over the portability service.
- `forge init` — idempotent, non-destructive workspace creation.

**Usability layer (V1.1)**
- `forge doctor` (environment + config checks), `forge status` (workspace at a glance),
  and `forge wizard` (guided first run).
- `forgeos` console alias alongside `forge` (same CLI).

**Install & docs**
- One-command installer: `install.sh` (macOS/Linux) and `install.ps1` (Windows) via
  `uv tool install`, with shell-path update.
- Architecture (Rev 3), implementation plan, ADRs 0001–0012, V1 scope lock, and release
  checklist. Documentation reconciliation: execution-agent naming unified
  (Architect/Engineer/QA/Reviewer/Security); MCP scoped to V2.

### Quality gates
- `ruff check` clean, `mypy` strict on `src/` clean (98 files), and `pytest
  -W error::UserWarning` green (244 tests) on the real toolchain.

### Known limitations
- **Live provider validation is post-release.** The Claude and Ollama adapters are
  implemented and unit-tested, but end-to-end validation against live providers — a real
  Claude generate, a real Ollama generate, and token reconciliation of provider-reported
  usage vs. estimates — was not run in the build environment (no network / API key /
  local Ollama). These are tracked as post-release validation, not V1 build deliverables.

### Deferred to V2
- MCP stdio transport and CLI↔MCP parity (a services-facade extraction is planned first).
- Full Skill Graph: lifecycle management, versioning, deprecation, search, invocation,
  and advanced skill governance. V1 ships only creation-via-commit, `skill list`, `skill show`.

[1.0.0]: https://github.com/your-org/forgeos/releases/tag/v1.0.0
