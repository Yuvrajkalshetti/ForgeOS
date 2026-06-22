# ForgeOS V1 Readiness Audit (from-scratch, evidence-based)

Method: direct inspection of `src/`, `tests/`, `docs/adr/`; full suite run (208
passed); greps for capability presence/absence. Claims cite files/tests as evidence.

## Per-capability matrix
| # | Capability | Planned | Implemented | Tested | Evidence | Missing | Deferred |
|---|---|---|---|---|---|---|---|
| 1 | Config/Ports/Observability | Y | Full | Y | `config/`, `ports/`, `observability/`; `test_config_loader`, `test_ports` | — | — |
| 2 | Storage (SQLite index + YAML truth) | Y | Full | Y | `adapters/storage/sqlite/*`; `test_sqlite_store`, `test_snapshot_store`, `test_migrations` | — | typed tables/indexes (ADR 0008) |
| 3 | Knowledge Portability (export/import/backup) | Y | **Partial** | Y (service) | `services/portability.py`; `test_portability` | **no `forge export/import/backup` CLI** | — |
| 4 | Memory Engine | Y | Full | Y | `core/memory/service.py`; `test_memory_service` | — | — |
| 5 | Memory Lifecycle | Y | Full | Y | `core/memory/lifecycle.py`; `test_memory_lifecycle` | — | — |
| 6 | Knowledge Graph | Y | Full | Y | `core/graph/*`; `test_graph_store/registry/snapshot/cli` | — | edge SQL indexes (ADR 0008) |
| 7 | Decision Graph | Y | **Partial** | Y (traversal) | Decision node + edges + `forge why` (`graph/store.py`) | dedicated decision service / ADR-mirroring | — |
| 8 | Skill Graph | Y | **Missing** | No | only `NodeType.SKILL` + `uses_skill` rule (`graph/registry.py`) | skill service/CRUD/lifecycle/approval | — |
| 9 | Repository Intelligence (provider-free) | Y | Full | Y | `core/repo_intel/*`; `test_repo_*`, `test_repo_intel_provider_free` | — | richer JS/TS module grouping |
| 10 | Context Compression (deterministic) | Y | Full | Y | `core/compression/*`; `test_card_*` | — | (provider prose removed by ADR 0009) |
| 11 | Context Assembly | Y | Full | Y | `core/context_assembly/*`; `test_context_assembler` | — | — |
| 12 | Token Intelligence | Y | Full | Y | `core/token_intel/*`; `test_token_ledger` | — | live provider actuals |
| 13 | Provider Layer (Claude/Ollama/stubs) | Y | Full (mocked) | Y | `adapters/providers/*`; `test_provider_adapters` (MockTransport) | live cloud verification | — |
| 14 | Provider Intelligence | Y | Full | Y | `core/provider_intel/*`; `test_provider_intel` | — | metric routing not auto-engaged |
| 15 | Agent Orchestrator (Execution) | Y | Full | Y | `core/orchestrator/*`; `test_orchestrator` | — | — |
| 16 | Learning Engine | Y | **Partial** | Y (emit only) | `core/learning/proposal.py` = emit/list | **approve/commit/review pipeline** | — |
| 17 | Advisory System (Mentor/Auditor + grounding) | Y (amend) | Full | Y | `core/advisory/*`; `test_advisory_*` (incl. boundaries, context, grounding) | — | advisory→learning proposals |
| 18 | CLI Adapter | Y | **Partial** | Y | `adapters/transport/cli/*` (11 commands) | `install`, `init`, `export/import/backup` | — |
| 19 | MCP Adapter (stdio) | Y | **Missing** | No | transport dir has only `cli/` | full MCP server + CLI↔MCP parity | socket/HTTP (V2) |
| 20 | User Knowledge Layer (L2 `~/.forgeos`) | Y | **Partial** | Y (config) | `config/loader.py` reads `~/.forgeos`; memory user scope | user-scope skills/workflow surface; backup CLI | — |
| 21 | Project Knowledge Layer (L3 `.forgeos`) | Y | Full | Y | `_shared.open_store`, snapshots under `.forgeos` | — | — |
| 22 | Determinism + Boundaries (cross-cutting) | Y | Full | Y | `test_import_guard`, `test_provider_free_engines`, `test_advisory_boundaries` | — | — |

## 1. Remaining V1 blockers
- **B1 Learning approve/commit/review** — only `emit_proposal`/`list_proposals` exist; V1 scope lists a full Learning Engine. (P7)
- **B2 MCP stdio adapter + CLI↔MCP parity** — absent; V1 scope says "supports MCP." (P7)
- **B3 Skill Graph service** — only an enum value + edge rule; no service. (P7)
- **B4 CLI bootstrap/portability commands** — `forge install`, `forge init`, `forge export|import|backup` not registered (services exist for the latter).
- **B5 Live provider verification** — adapters proven only via `httpx.MockTransport`; no real cloud/Ollama call (environment-limited).

## 2. Hidden architecture drift
- **D1 Execution agent naming mismatch (semi-hidden).** Implemented agents are
  `architect, engineer, qa, reviewer, security` (`core/orchestrator/agents.py`) —
  matching the *original* Architecture §Agent System. The Advisory **amendment**
  labelled the Execution System `Planner, Researcher, Coder, Reviewer, Tester`. Two
  approved docs disagree; not reconciled anywhere. Functional, but a naming drift.
- No other undocumented drift found. Compression→deterministic (ADR 0009) and
  ranking float→tiers (ADR 0011) are **documented** decisions, not drift.

## 3. Scope creep
- **Mild:** metric routing policies (`cheapest/fastest/most_reliable` in
  `provider_intel/router.py`) exceed the V1 "pinned only" wiring — implemented but
  not engaged. Harmless, tested.
- **Sanctioned:** `AdvisorySession` (amendment "add if simple"), `AdvisoryContextBuilder`
  + grounding (P6.6 approved). Not creep.
- **Non-product:** `scripts/check.py` is an environment substitute for ruff/mypy, not
  a shipped feature.

## 4. Missing acceptance criteria
- No AC defined/verified for: **MCP parity** (plan A10 unmet), **Skill Graph**,
  **Learning approve/commit**, **CLI install/init/export**, **L2 user-layer behaviors**,
  **live-provider smoke**.
- **Coverage %** unmeasured: plan implies core ≥90% but no coverage tool runs in this
  environment (asserted per-module/per-branch instead).

## 5. Features implemented but not planned
- Metric routing policies (see §3) — beyond V1 default.
- `ContextBundle.render()`, `grounding_refs`, deterministic `TIER` table — introduced by
  approved P6.6/ADR 0011 (planned in that scope).
- `scripts/check.py` substitute gate (environment, not product).

## 6. Planned features not implemented
- MCP adapter (B2) · Skill Graph service (B3) · Learning approve/commit (B1) ·
  `forge install/init/export/import/backup` (B4) · dedicated Decision Graph service
  (item 7 partial) · live provider path (B5).

## Final V1 readiness verdict
**Not yet V1-complete.** Foundation through Advisory (items 1–17, 21–22) are
implemented + tested with evidence (208 tests green). **Five blockers remain**, all
concentrated in the planned-but-unstarted **P7** band (Learning, MCP, Skill Graph)
plus CLI bootstrap/portability wiring (B4) and a live-provider smoke (B5). One naming
drift (D1) should be reconciled in docs. No destructive scope creep.

Readiness (capabilities at Full + Tested): **15 / 22**. Partial: 5 (3,7,16,18,20).
Missing: 2 (8 Skill Graph, 19 MCP).
