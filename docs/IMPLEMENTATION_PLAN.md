# ForgeOS — Implementation Plan (Gate 2)

> Status: **Approved & largely implemented** (P0–P6.6 + human-gated Learning + minimal Skill
> promotion + portability/init CLI). Companion: `docs/ARCHITECTURE.md`.
>
> **⚠️ V1 scope reconciliation (2026-06-21, ADR 0012):** **V1 = CLI-first.** **MCP adapter
> + CLI↔MCP parity → V2.** **Full Skill Graph → V2;** V1 ships **minimal Skill promotion**
> (Skill node via approved Learning commit + `forge skill list|show`). Sections below that
> place MCP or a full Skill Graph in V1/P7 are **superseded by ADR 0012** and annotated
> inline. Authoritative: `docs/SCOPE-V1.md`, `docs/AMENDMENT-v1-scope.md`.

## Approved decisions (binding)
- **Runtime:** Python **3.12**. **uv** (env + deps), **ruff** (lint+format), **pytest** (tests), **mypy** (typing, strict on `core/`).
- **MCP:** **deferred to V2 (ADR 0012); V1 is CLI-first.** stdio remains the chosen transport design when built.
- **Backup:** manual (git-native + `forge backup`); no scheduler.
- **Concurrency:** real bounded `asyncio` (global + per-provider semaphores), deterministic merge.
- **Compression:** fixed core schema + open `extensions.x_*` blocks.
- **Token accounting:** dual source (local estimate pre-flight + provider-reported actual).

## Hard directive — Repository Intelligence Engine
RepoIntel is **deterministic and provider-free**. **No provider/LLM calls** during: repository scanning, graph construction, dependency discovery, hotspot analysis, or incremental indexing. Enforced by (a) RepoIntel package not importing the `Provider` port, and (b) a unit test asserting no provider invocation across the ingest path (fake provider that fails if called).

---

## 1. Implementation Phases

Eight phases; each ends green (lint+type+test) and independently demoable.

| Phase | Name | Delivers | Exit signal |
|---|---|---|---|
| P0 | Foundation | repo, uv project, CI, config loader, port interfaces, fakes | `uv run pytest` green; `forge --help` |
| P1 | Storage & Persistence | SQLite adapter, YAML snapshot sync, migrations, export/import/backup | round-trip test passes |
| P2 | Memory & Lifecycle | Memory CRUD (4 scopes), TTL/decay/dedup, `memory gc` | lifecycle policy tests pass |
| P3 | Knowledge Graph | nodes/edges, bounded traversal, snapshots, `graph query`/`why` | traversal + snapshot tests |
| P4 | Repository Intelligence | scan, dep map, hotspots, incremental index — **provider-free** | provider-free assertion test |
| P5 | Token + Compression + Assembly | TokenIntel, knowledge cards, ContextAssembly + manifest | savings + budget tests |
| P6 | Providers + Orchestrator | Claude/Ollama adapters, ProviderIntel, 5 agents, async merge | live-adapter smoke + merge determinism |
| P7 | Learning + Transports | Learning pipeline + minimal Skill, **CLI complete (V1)**; **MCP stdio parity → V2 (ADR 0012)** | CLI surfaces the loop (V1); parity tests → V2 |

---

## 2. Work Breakdown Structure

```
P0 Foundation
  0.1 uv project, pyproject, console entry `forge`
  0.2 ruff + mypy(strict core) + pytest config; pre-commit
  0.3 CI (lint, type, test matrix)
  0.4 layered config loader (defaults → ~/.forgeos → project/.forgeos → env)
  0.5 ports: storage, provider, transport, tokenizer, vector(stub)
  0.6 fakes for every port; logging/observability bootstrap

P1 Storage & Persistence
  1.1 SQLite schema + migration runner (versioned)
  1.2 generic node/edge + memory + token_events + provider_stats DAOs
  1.3 YAML/JSON snapshot writer + loader (write-through)
  1.4 export / import / backup services + bundle format + schema_version
  1.5 round-trip + divergence-recovery tests

P2 Memory & Lifecycle
  2.1 memory record model + validation
  2.2 CRUD across scopes; graph-link writes
  2.3 lifecycle: TTL, decay (salience), dedup (content hash)
  2.4 consolidation/promotion → emits Learning proposal (no auto-apply)
  2.5 `forge memory add|query|gc`

P3 Knowledge Graph
  3.1 node/edge domain types + typed edge registry
  3.2 bounded BFS traversal + typed filters
  3.3 graph snapshot sync
  3.4 `forge graph query`, `forge why <module>` (decision traversal)

P4 Repository Intelligence  (PROVIDER-FREE)
  4.1 file walker + language detection + ignore rules
  4.2 dependency discovery (Python + JS/TS first-class; heuristic fallback)
  4.3 git-churn hotspot analysis
  4.4 content-hash incremental index (only changed files re-ingested)
  4.5 emit File/Module/Dependency nodes + edges + repo_profile
  4.6 `forge scan`; provider-free assertion test

P5 Token + Compression + Assembly
  5.1 TokenizerPort adapters: local estimator + provider-reported actual
  5.2 budgets + savings accounting (token_events) + `forge tokens report`
  5.3 knowledge card schema (JSON Schema) + generator (lazy + bulk) + source_hash invalidation
  5.4 ContextAssembly: seed→expand→rank→budget→assemble + manifest
  5.5 `forge compress`, `forge context build`

P6 Providers + Orchestrator
  6.1 Provider port impls: Claude, Ollama; OpenAI/Gemini stubs
  6.2 ProviderIntel stats capture + `forge provider stats`
  6.3 agent definitions (Architect/Engineer/QA/Reviewer/Security)
  6.4 async orchestrator: semaphores, timeout, retry, failure-isolation
  6.5 deterministic merge reducer; `forge agent run`

P7 Learning + Transports
  7.1 Learning proposal store + review/approve/reject/commit (+ minimal Skill promotion)
  7.2 CLI surface completion (learn / skill / export / import / backup / init) + help/UX
  7.3 MCP stdio server: Memory/Graph/Skill/Agent/Project services   # → V2 (ADR 0012)
  7.4 CLI↔MCP parity test suite                                     # → V2 (ADR 0012)
```

---

## 3. Package Structure

```
src/forgeos/
  core/
    memory/        {models.py, lifecycle.py, service.py}
    repo_intel/    {scanner.py, deps.py, hotspots.py, index.py}   # NO provider import
    compression/   {schema.py, cards.py, generator.py}
    context_assembly/ {assembler.py, ranker.py, budget.py, manifest.py}
    token_intel/   {counter.py, budgets.py, savings.py}
    graph/         {models.py, store.py, traversal.py}
    decision/      {models.py, service.py}
    skill/         {models.py, service.py}
    learning/      {proposal.py, pipeline.py}
    provider_intel/{stats.py, scorecard.py}
    orchestrator/  {agents.py, runner.py, merge.py}
  ports/           {storage.py, provider.py, transport.py, tokenizer.py, vector.py}
  adapters/
    storage/sqlite/{schema.py, migrations/, dao.py, snapshots.py}
    providers/{claude/, ollama/, stubs/}
    tokenizer/{local.py, provider_reported.py}
    transport/{cli/, mcp/}
  services/        # use-case orchestration wiring core + ports
  config/          {loader.py, models.py}
tests/{unit,integration,fixtures}/
```
**Invariant:** `core/` never imports `adapters/`; `core/repo_intel/` never imports `ports/provider.py`.

---

## 4. Data Models

Pydantic v2 models (validation + serialization). Key models:

```python
MemoryRecord: id, scope, kind, content, source{type,ref},
  created_at, updated_at, last_accessed_at, access_count,
  salience, ttl?, status, links[node_id]
Node: id, type, label, props{}, created_at, updated_at
Edge: id, src_id, dst_id, type, props{}, created_at
KnowledgeCard: schema_version, card_id, target{type,ref}, generated_at,
  source_hash, provider{name,model}, purpose, modules[], dependencies[],
  key_decisions[], risks[], recent_changes[], extensions{x_*}
Decision: (Node subtype) title, status, rationale, evidence[],
  alternatives[], approved_by, approved_at
Skill: (Node subtype) name, intent, steps[], inputs, outputs,
  evidence_of_value, reuse_count, status, approved_by, approved_at
LearningProposal: id, kind, payload, evidence[], benefits, risks,
  reuse_value, token_savings_est, status, created_at, resolved_at?
ContextBundle: items[], manifest[], total_tokens, dropped[]
TokenEvent: id, request_id, scope_ref, provider, model,
  tokens_estimated, tokens_actual, tokens_raw_equiv, tokens_saved, created_at
ProviderStat: provider, model, calls, tokens_in, tokens_out, est_cost,
  avg_latency_ms, p95_latency_ms, success_rate, error_breakdown, capabilities, last_seen_at
RepoProfile: project_ref, languages[], entry_points[], module_count,
  hotspots[], scanned_at, index_hash
```

---

## 5. Database Schema (SQLite — derived/rebuildable)

```sql
-- graph
nodes(id TEXT PK, type TEXT, label TEXT, props_json TEXT, created_at, updated_at);
edges(id TEXT PK, src_id TEXT, dst_id TEXT, type TEXT, props_json TEXT, created_at,
      FOREIGN KEY(src_id) REFERENCES nodes(id), FOREIGN KEY(dst_id) REFERENCES nodes(id));
CREATE INDEX idx_edges_src ON edges(src_id, type);
CREATE INDEX idx_edges_dst ON edges(dst_id, type);
CREATE INDEX idx_nodes_type ON nodes(type);

-- memory
memory(id TEXT PK, scope TEXT, kind TEXT, content TEXT, source_json TEXT,
       created_at, updated_at, last_accessed_at, access_count INT,
       salience REAL, ttl TEXT, status TEXT);
CREATE INDEX idx_memory_scope ON memory(scope, status);
memory_links(memory_id TEXT, node_id TEXT, PRIMARY KEY(memory_id,node_id));

-- knowledge cards
cards(card_id TEXT PK, target_type TEXT, target_ref TEXT, source_hash TEXT,
      schema_version INT, payload_json TEXT, provider TEXT, model TEXT, generated_at);
CREATE INDEX idx_cards_target ON cards(target_type, target_ref);

-- token + provider intelligence
token_events(id TEXT PK, request_id TEXT, scope_ref TEXT, provider TEXT, model TEXT,
             tokens_estimated INT, tokens_actual INT, tokens_raw_equiv INT,
             tokens_saved INT, created_at);
provider_stats(provider TEXT, model TEXT, calls INT, tokens_in INT, tokens_out INT,
               est_cost REAL, avg_latency_ms REAL, p95_latency_ms REAL,
               success_rate REAL, error_breakdown_json TEXT, capabilities_json TEXT,
               last_seen_at, PRIMARY KEY(provider, model));

-- learning
proposals(id TEXT PK, kind TEXT, payload_json TEXT, evidence_json TEXT,
          benefits TEXT, risks TEXT, reuse_value TEXT, token_savings_est INT,
          status TEXT, created_at, resolved_at);

-- meta
schema_meta(key TEXT PK, value TEXT);   -- schema_version, etc.
```
Snapshots (YAML/JSON in git) are the **source of truth**; this DB is rebuildable from them.

---

## 6. Graph Schema

- **Node types:** File, Module, Dependency, Decision, Skill, Agent, Project, MemoryRef, KnowledgeCard.
- **Edge types (typed registry, validated on write):**
  `contains` (Module→File), `depends_on` (Module/File→Dependency/Module),
  `decided_by` (File/Module→Decision), `affects` (Decision→File/Module),
  `supersedes` (Decision→Decision), `summarized_by` (target→KnowledgeCard),
  `uses_skill` (Agent/Project→Skill), `derived_from` (MemoryRef→source), `relates_to` (generic).
- **Traversal:** bounded BFS with `(max_depth, allowed_edge_types, node_type_filter)`.
- **Snapshots:** `graph/nodes.yaml`, `graph/edges.yaml` per scope.

---

## 7. CLI Command Design

`forge` (Typer/Click-style), every command routes through `services/`:

| Command | Purpose | Phase |
|---|---|---|
| ~~`forge install`~~ | **removed from V1** — install via `uv tool install` / pip (ADR 0012) | — |
| `forge init` | create `<project>/.forgeos` (L3); idempotent | V1 |
| `forge scan [path]` | RepoIntel ingest/refresh (provider-free) | P4 |
| `forge compress <path> [--bulk]` | generate/refresh knowledge card | P5 |
| `forge memory add\|query\|gc` | memory ops; gc = lifecycle pass | P2 |
| `forge graph query <expr>` / `forge why <module>` | traversal / decision lookup | P3 |
| `forge context build <task> [--budget N]` | assembly preview + manifest | P5 |
| `forge tokens report` | savings/budget report | P5 |
| `forge learn review\|approve\|reject\|commit` | human-gated learning | V1 |
| `forge skill list\|show` | minimal Skill (full Skill Graph → V2, ADR 0012) | V1 |
| `forge agent run <set>` | orchestrated multi-agent run | P6 |
| `forge provider use <name>` / `forge provider stats` | provider select / scorecards | P6 |
| `forge export\|import\|backup` | portability + backup | P1 |

Global flags: `--project`, `--json`, `--verbose`. Exit codes standardized.

---

## 8. MCP Service Design (stdio) — **DEFERRED TO V2 (ADR 0012)**

> The MCP adapter is **not in V1** (V1 is CLI-first). This design is retained for **V2**; the
> transport seam + shared `services/` layer are preserved so it is purely additive later.

MCP server is a transport adapter over the same `services/`. Tools exposed:

| MCP tool | Maps to service | Notes |
|---|---|---|
| `memory.add` / `memory.query` | Memory service | mirrors CLI |
| `graph.query` / `graph.why` | Graph service | bounded traversal |
| `context.build` | ContextAssembly | returns bundle + manifest |
| `skill.list` / `skill.propose` | Skill/Learning | approve stays human/CLI-gated |
| `agent.run` | Orchestrator | async run, returns merged findings |
| `project.scan` / `project.info` | RepoIntel/Project | provider-free scan |

- **Resources:** read-only knowledge cards + repo_profile exposed as MCP resources.
- **Parity requirement:** every MCP tool has a CLI equivalent backed by the identical service call; verified by parity tests (§11).
- **No write-side autonomy:** approvals/commits are not exposed as auto-callable MCP tools in V1.

---

## 9. Agent Runtime Design

- **Agents:** Architect, Engineer, QA, Reviewer, Security — each a declarative spec `{role, system_prompt, required_context, output_schema}`.
- **Output contract:** structured findings `{claim, evidence[], confidence, severity, alternatives[]}`.
- **Runner (asyncio):**
  ```
  build per-agent ContextBundle (via ContextAssembly, budgeted)
  asyncio.gather(tasks) under Semaphore(global) + Semaphore(per-provider)
  per-call: timeout, retry-with-backoff, capture errors as findings (isolation)
  ```
- **Merge (deterministic):** collect → sort by `(agent, severity, -confidence, claim_hash)` → dedup → attach evidence/provenance → emit report. Reproducible regardless of completion order.
- **Observability:** each agent run records tokens (§TokenIntel), latency, provider (§ProviderIntel).

---

## 10. Provider Integration Design

- **ProviderPort:** `async generate(messages, model, **opts) -> ProviderResult{text, usage, latency, raw}`.
- **Claude adapter:** Anthropic SDK; reads usage from response; model id from config (default latest Claude).
- **Ollama adapter:** local HTTP; maps eval counts → usage; lower default concurrency.
- **Stubs (OpenAI/Gemini):** implement interface, raise `NotImplementedError` with guidance.
- **Secrets:** keys via env/OS keychain only; never persisted to snapshots.
- **ProviderIntel hook:** every call emits a stats event → `provider_stats` + `token_events`.
- **Routing (V1):** explicit config policy (`cheapest-capable` / `fastest` / `pinned`); no autonomous switching.
- **Contract tests:** recorded-fixture tests so adapters are testable without live keys.

---

## 11. Testing Strategy

- **Unit (fast, no I/O):** core domain against fakes; mypy-strict on `core/`. Pure functions for ranking/merge/lifecycle/dedup.
- **Provider-free assertion test (P4):** ingest path run with a fake provider that raises on call → must pass.
- **Integration:** SQLite + snapshot round-trip; export/import/backup; incremental rescan idempotence.
- **Contract tests:** provider adapters against recorded fixtures (no live keys in CI).
- **CLI↔MCP parity:** table of operations asserting identical service results via both transports.
- **Determinism tests:** orchestrator merge stable under shuffled completion order; graph traversal deterministic.
- **Property tests (where valuable):** dedup/lifecycle invariants.
- **Coverage gate:** core ≥ 90%; adapters ≥ 70%. CI: `ruff` + `mypy` + `pytest`.

---

## 12. Migration Strategy

- **Schema versioning:** `schema_meta.schema_version`; numbered migrations in `adapters/storage/sqlite/migrations/`.
- **Forward-only migrations** for V1; each migration idempotent + tested.
- **Snapshot is canonical:** on version mismatch or corruption, **rebuild SQLite from snapshots** rather than in-place upgrade where feasible.
- **Bundle compatibility:** `forge import` validates `schema_version`; refuses newer-than-supported with a clear message; migrates older bundles.
- **Card schema evolution:** `knowledge_card.schema_version` independent of DB version; old cards re-generated lazily on `source_hash`/version change.

---

## 13. Observability Strategy

- **Structured logging:** JSON logs with `request_id` correlating CLI/MCP → service → provider call.
- **Metrics surfaced via CLI (no external stack in V1):** `forge tokens report` (savings/budget), `forge provider stats` (latency/cost/success).
- **Audit trail:** every learning/decision/lifecycle action logged with who/what/when (provenance).
- **Assembly manifest:** every ContextAssembly run records included/dropped items + token cost — debuggable token decisions.
- **Run records:** orchestrator runs persisted with per-agent evidence + timings for replay/inspection.

---

## 14. Acceptance Criteria

| # | Criterion |
|---|---|
| A1 | `uv run` brings up env; `ruff`, `mypy`, `pytest` all green in CI. |
| A2 | `forge init` creates `.forgeos/`; `export`→`import` reproduces identical graph+memory (round-trip). |
| A3 | Memory lifecycle: session TTL expiry + dedup verified; durable consolidation produces a **proposal**, never auto-applies. |
| A4 | `forge scan` builds graph with **zero provider calls** (assertion test passes); incremental rescan re-ingests only changed files. |
| A5 | Knowledge card validates against JSON Schema; invalidates on source change; `extensions.x_*` accepted. |
| A6 | `forge context build` stays within budget; manifest lists included + dropped with token costs. |
| A7 | `forge tokens report` shows `tokens_saved` reconciling estimate vs provider-reported actual. |
| A8 | `forge agent run` executes 5 agents concurrently, bounded by semaphores, with a **deterministic** merged report. |
| A9 | `forge provider stats` reflects real latency/token/cost per provider/model. |
| A10 | *(V2 — ADR 0012; **not a V1 criterion**)* MCP stdio server exposes the defined tools; CLI↔MCP parity tests pass. V1 ships the equivalent **CLI** surface. |
| A11 | No secret ever written to snapshots/git; `.gitignore` enforced. |
| A12 | RepoIntel package does not import the Provider port (static check + test). |

---

## 15. Build Order

```
P0 Foundation
  → P1 Storage (everything persists through this)
    → P2 Memory+Lifecycle ─┐
    → P3 Graph ────────────┤→ both needed before assembly
      → P4 RepoIntel (provider-free; depends on Graph+Storage)
        → P5 Token + Compression + Assembly (depends on Graph, RepoIntel, Token)
          → P6 Providers + Orchestrator (depends on Assembly + Token + ProviderIntel)
            → P7 Learning + Transports (CLI complete in V1; MCP parity → V2, ADR 0012)
```
Rationale: storage first (nothing works without persistence), graph + memory before assembly (assembly reads them), RepoIntel before compression (cards consume repo signals), providers/orchestrator after assembly (they need budgeted bundles), transports + learning last (surface + governance over a working core).

---

## 16. Estimated Complexity and Risks

| Phase | Complexity | Primary risk | Mitigation |
|---|---|---|---|
| P0 | Low | toolchain/CI friction | pin versions; thin first slice |
| P1 | **High** | SQLite↔snapshot sync correctness | snapshot = source of truth; round-trip tests early |
| P2 | Med | lifecycle deleting useful memory | archive-first; durable changes are proposals |
| P3 | Med | traversal performance/cycles | bounded depth; visited-set; indexes |
| P4 | **High** | language-specific dep parsing breadth | Python+JS/TS first-class, heuristic fallback; never block |
| P5 | **High** | assembly under/over-context; savings accuracy | manifest visibility; budget escalation; dual tokenizer reconcile |
| P6 | **High** | async correctness; provider drift; local Ollama load | semaphores+timeouts; contract fixtures; low Ollama concurrency |
| P7 | Med | CLI↔MCP drift | shared services layer + parity tests |

**Cross-cutting risks:** scope creep into V1-excluded items (gate via ADRs + token-efficiency test); secret leakage (keychain/env + enforced `.gitignore` + import validation); determinism regressions (dedicated determinism tests in CI).

---

## Next step
Awaiting **Gate 2 approval of this Implementation Plan**. On approval, implementation begins at **P0**, TDD per phase (`Test → Implement → Validate`), each phase ending lint+type+test green before the next.
