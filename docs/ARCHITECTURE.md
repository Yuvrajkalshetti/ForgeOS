# ForgeOS — Architecture & V1 Roadmap

> Status: **Rev 3 (+ V1 scope reconciliation, 2026-06-21).** P0–P6.6 implemented;
> Advisory System (P6.5) accepted (ADR 0010) and grounded (ADR 0011); human-gated Learning
> + minimal Skill promotion + portability CLI implemented.
>
> **⚠️ V1 scope is LOCKED — authoritative: `docs/SCOPE-V1.md`, `docs/AMENDMENT-v1-scope.md`, ADR 0012.**
> **V1 = CLI-first.** **MCP adapter + CLI↔MCP parity → V2.** **Full Skill Graph
> (lifecycle/versioning/search/invocation) → V2;** V1 ships **minimal Skill promotion**
> (Skill nodes via approved Learning commit + `forge skill list|show`). Where older sections
> below describe MCP or a full Skill Graph as V1, they are **superseded by ADR 0012** and
> annotated inline.
> Execution agents are **Architect / Engineer / QA / Reviewer / Security** (single
> authoritative set; §16).

### Rev 3 changelog (amendment)
- **Added subsystem:** Advisory System (Mentor + Auditor), separate from Execution. See **ADR 0010** and **`docs/AMENDMENT-advisory-system.md`** for the full amendment, impact, and migration.
- Graph gains node types `MentorRecommendation`, `AuditFinding` and edges `advises`, `informs`, `audits` (additive; §7).
- Roadmap gains **P6.5 — Advisory System** (after P6, before P7).

### Rev 2 changelog
- **Added components:** Repository Intelligence Engine (§8), Context Assembly Engine (§10), Token Intelligence Engine (§11), Memory Lifecycle Management (§5), Provider Intelligence Tracking (§15).
- **Clarified:** Compression schema (§9), Parallel execution strategy (§16), Backup strategy (§22).
- Updated component table, repo structure, roadmap, risks, tradeoffs, open questions accordingly.

## Clarified Decisions (locked with stakeholder)

| Decision | Choice | Rationale |
|---|---|---|
| Repository | New standalone repo (`~/code/forgeos`) | Honors "dedicated standalone repository" rule; sandbox blocked `Documents/GitHub`, so `~/code` used instead. |
| Graph/Memory storage | SQLite + JSON/YAML | Local-first, zero external service deps, portable, trivial backup/restore. |
| Retrieval (V1) | Graph traversal + structured query only | Matches "do not rely solely on vector search"; embeddings deferred to V2 behind an adapter seam. |
| Providers | Claude + Ollama both wired | Proves cloud + local abstraction on day one; OpenAI/Gemini interface-stubbed. |

---

## 1. Architecture Document

ForgeOS is a **local-first AI Operating System** mediating between users, projects, and AI providers. It is a long-lived Python service + CLI whose job is to **preserve knowledge while sending fewer tokens**.

### 1.1 Architectural style
- **Layered + adapter-first (hexagonal/ports-and-adapters).** A pure core surrounded by swappable adapters (providers, transports, storage).
- **Local-first, cloud-optional.** All knowledge lives on disk in open formats. Cloud is only an outbound provider call; losing the cloud never loses knowledge.
- **Knowledge is the asset; runtime is disposable.** Reinstalling the runtime must never destroy knowledge.

### 1.2 High-level shape
```
                ┌──────────────────────────────────────────────┐
   CLI ─────────┤   TRANSPORT ADAPTERS  (CLI, MCP; later REST) │
   MCP server ──┤                                              │
                └───────────────┬──────────────────────────────┘
                                │  Application Services (use-cases)
   ┌────────────────────────────▼─────────────────────────────────┐
   │                         CORE DOMAIN                            │
   │  INGEST          KNOWLEDGE         REQUEST-TIME      GOVERNANCE │
   │  ──────          ─────────         ────────────      ───────── │
   │  RepoIntel  →    KnowledgeGraph    ContextAssembly   Learning  │
   │  Compression →   DecisionGraph  →  TokenIntel        MemoryLife │
   │                  SkillGraph        Orchestrator      ProviderIntel
   │                  Memory                                        │
   └───────┬─────────────────────┬──────────────────────┬──────────┘
           │                     │                      │
   ┌───────▼───────┐   ┌─────────▼─────────┐   ┌─────────▼─────────┐
   │ STORAGE PORT  │   │  PROVIDER PORT    │   │  VECTOR PORT (V2, │
   │ SQLite + YAML │   │ Claude · Ollama · │   │  off by default)  │
   │ /JSON repos   │   │ (OpenAI/Gemini)   │   │                   │
   └───────────────┘   └───────────────────┘   └───────────────────┘
```

### 1.3 Data-flow spine (how the engines chain)
```
RepoIntel  →  Compression  →  KnowledgeGraph + Memory   (write path / ingest)
Query/Task →  ContextAssembly  →  TokenIntel (budget)  →  Provider  →  Orchestrator
Session    →  MemoryLifecycle  →  Learning (propose)  →  human approve  →  commit
Every call →  TokenIntel + ProviderIntel  (measure savings, latency, cost)
```

### 1.4 Knowledge tiers (the four layers)
- **L1 Runtime** — machine-specific, reinstallable. Code, services, MCP server, CLI, orchestrator.
- **L2 User Knowledge** — `~/.forgeos/` — preferences, approved skills, workflows, provider prefs. Portable.
- **L3 Project Knowledge** — `<project>/.forgeos/` — memory, summaries, graphs, skills, learnings. Travels with the repo.
- **L4 Org Knowledge** — optional, design-for-but-not-built in V1.

---

## 2. Repository Structure

```
forgeos/
├── README.md
├── pyproject.toml                 # packaging, console entrypoint `forge`
├── docs/
│   ├── ARCHITECTURE.md            # this document
│   ├── adr/                       # architecture decision records
│   └── schemas/                   # JSON Schemas for knowledge artifacts
├── src/forgeos/
│   ├── core/                      # PURE domain — no I/O, no provider calls
│   │   ├── memory/                # records + lifecycle policies
│   │   ├── repo_intel/            # repository intelligence
│   │   ├── compression/           # knowledge cards
│   │   ├── context_assembly/      # request-time context builder
│   │   ├── token_intel/           # token counting / budgets / savings
│   │   ├── graph/                 # knowledge graph primitives (nodes/edges)
│   │   ├── decision/
│   │   ├── skill/
│   │   ├── learning/
│   │   ├── provider_intel/        # provider scorecards / routing inputs
│   │   └── orchestrator/
│   ├── ports/                     # abstract interfaces (Protocols/ABCs)
│   │   ├── storage.py
│   │   ├── provider.py
│   │   ├── transport.py
│   │   ├── tokenizer.py           # token counting port
│   │   └── vector.py              # defined, unused in V1
│   ├── adapters/
│   │   ├── storage/sqlite/
│   │   ├── providers/claude/
│   │   ├── providers/ollama/
│   │   ├── providers/stubs/       # openai, gemini
│   │   ├── tokenizer/             # provider-reported + local estimator
│   │   └── transport/{cli,mcp}/
│   ├── services/                  # application use-cases wiring core+ports
│   └── config/                    # layered config loader
├── tests/{unit,integration,fixtures}/
└── scripts/                       # install/upgrade/backup helpers
```

**Rule:** `core/` imports nothing from `adapters/`. Dependencies point inward only.

---

## 3. Component Design

| # | Component | Responsibility | Key interfaces |
|---|---|---|---|
| 1 | Repository Intelligence Engine | Scan repos → structure, modules, deps, hotspots; seed graph | `StoragePort`, emits graph nodes |
| 2 | Context Compression Engine | Turn raw repos/files into compact knowledge cards | `Provider`, `RepoIntel`, graph |
| 3 | Context Assembly Engine | Build minimal token-budgeted context per task | graph + memory + cards + `TokenIntel` |
| 4 | Token Intelligence Engine | Count/estimate tokens, budgets, measure savings | `TokenizerPort` |
| 5 | Memory Engine | CRUD session/project/user/learning memory | `MemoryStore` |
| 6 | Memory Lifecycle Management | TTL, decay, consolidation, promotion, eviction | `MemoryStore`, feeds Learning |
| 7 | Knowledge Graph | Nodes/edges over files, modules, deps, decisions, skills | `GraphStore` |
| 8 | Decision Graph | ADR-style decisions + rationale + approval history | extends `GraphStore` |
| 9 | Skill Graph | Reusable approved patterns. **V1: minimal** (Skill nodes via approved commit; `skill list/show`). **Full Skill Graph → V2 (ADR 0012).** | extends `GraphStore` |
| 10 | Learning Engine | Observe → propose → human-approve → commit | `ProposalStore` |
| 11 | Provider Layer | Normalize Claude/Ollama/… behind one interface | `Provider` |
| 12 | Provider Intelligence Tracking | Per-provider cost/latency/quality scorecards → routing | `StoragePort`, feeds Orchestrator |
| 13 | Agent Orchestrator | Run 5 agents (parallel), merge evidence-backed findings | `Provider`, `ProviderIntel` |
| 14 | Transport Adapters | **V1: CLI.** **MCP → V2 (ADR 0012)** (transport seam preserved). | `Transport` |

Each component is a package with a narrow public API and unit tests against fakes (no live providers in unit tests).

---

## 4. Memory Model

Four scopes, one shape. Every memory record:
```yaml
id: mem_<ulid>
scope: session | project | user | learning
kind: fact | summary | preference | event | observation
content: <text or structured payload>
source: {type, ref}          # provenance / evidence
created_at, updated_at, last_accessed_at
access_count: 0              # used by lifecycle decay/promotion
salience: 0.0..1.0           # lifecycle ranking signal
ttl: optional                # session memory may expire
status: active | archived    # lifecycle state
links: [node_ids]            # ties memory into the knowledge graph
```
- **Session:** ephemeral working set; consolidated at session end (via a *learning proposal*, never silent overwrite).
- **Project:** durable, `<project>/.forgeos/memory.sqlite` + YAML snapshots for git diff/review.
- **User:** `~/.forgeos/`.
- **Learning:** observations awaiting promotion.

Queryable via the graph (links) and structured filters (scope/kind/time/salience).

---

## 5. Memory Lifecycle Management  *(NEW)*

Governs how memory is born, ages, consolidates, and retires — so memory stays small, relevant, and cheap to assemble. **No destructive action without a rule + audit trail; consolidation of durable memory is proposed, not auto-applied.**

### 5.1 Lifecycle states
```
created → active → (consolidated) → archived → (purged, session-scope only)
```

### 5.2 Policies (config-driven, per scope)
| Mechanism | Behavior | Default |
|---|---|---|
| **TTL / expiry** | Session memory expires after inactivity | session: 24h; project/user: none |
| **Decay** | `salience` decays over time; boosted on access | half-life 14d (project) |
| **Promotion** | Recurring/high-salience session facts → *proposal* to project memory | threshold-based |
| **Consolidation** | Merge duplicate/overlapping records into one summary | proposal for durable scopes |
| **Eviction** | Drop expired session memory; archive (never delete) durable memory | archive-first |
| **Dedup** | Content hash + link overlap detection on write | always on |

### 5.3 Triggers
- On write (dedup), on access (salience boost), at session end (consolidation pass), and via explicit `forge memory gc`.
- Durable-scope consolidation/promotion always routes through the **Learning Engine** (human approval). Session-scope eviction is automatic and logged.

---

## 6. Knowledge Architecture

- **Open formats first:** SQLite as query engine; **YAML/JSON snapshots committed to git** as the human-readable, portable, diffable source of truth. SQLite is a rebuildable cache/index derived from snapshots.
- **Portability guarantee:** `forge export` produces a self-contained bundle; `forge import` rebuilds SQLite from snapshots on any machine.
- **Provenance everywhere:** every node/edge/memory carries a `source` so claims can be justified without re-reading source code.

---

## 7. Knowledge Graph Design

Generic property-graph in SQLite:
```sql
nodes(id, type, label, props_json, created_at, updated_at)
edges(id, src_id, dst_id, type, props_json, created_at)
```
- **Node types (V1):** File, Module, Dependency, Decision, Skill, Agent, Project, MemoryRef, KnowledgeCard; **+ Advisory (ADR 0010): MentorRecommendation, AuditFinding.**
- **Edge types:** depends_on, contains, decided_by, affects, derived_from, uses_skill, summarized_by, relates_to; **+ Advisory: advises, informs, audits.**
- **Advisory lineage:** `MentorRecommendation --informs--> Decision(human) --affects--> File/Module <--audits-- AuditFinding`.
- **Retrieval:** graph traversal (BFS/bounded-depth) + typed filters is the **primary** mechanism. Vector recall is explicitly out for V1.
- Snapshots: `graph/nodes.yaml`, `graph/edges.yaml` per project for git.

---

## 8. Repository Intelligence Engine  *(NEW)*

The **ingestion brain**: turns a raw repository into structured graph + signals that Compression and Context Assembly consume. Deterministic, local, no provider calls (cheap, repeatable).

### 8.1 Responsibilities
- **Structure discovery:** language(s), package/module boundaries, entry points, config/build files.
- **Dependency mapping:** import/require graph → `depends_on` / `contains` edges.
- **Hotspot detection:** churn from git history (commit frequency, recent changes) → `Recent Changes` signal for cards.
- **Ownership/metadata:** top contributors, last-modified, size — as node props.
- **Incremental rescans:** content-hash per file; only changed files re-ingested (token + compute efficient).

### 8.2 Output
- Graph nodes/edges (File, Module, Dependency) with provenance.
- A `repo_profile` record feeding the Compression Engine and ranking signals (hotspots) for Context Assembly.

### 8.3 Boundaries
- Pure static analysis in V1 (language-aware parsers where available, regex/heuristic fallback). No semantic/LLM analysis here — that belongs to Compression.

---

## 9. Context Compression Engine  *(schema CLARIFIED)*

Transforms raw repos/modules into compact, reusable **knowledge cards**, so we send cards instead of source.

### 9.1 Compression schema — DECISION
**Fixed core schema (required, stable, versioned) + optional extension blocks (project-defined).** This keeps cards diffable/queryable while allowing project-specific enrichment without breaking the core contract.

```yaml
# forgeos.knowledge_card v1
schema_version: 1
card_id: card_<ulid>
target:                       # what this card summarizes
  type: repo | module | file | subsystem
  ref: <path or node_id>
generated_at: <iso8601>
source_hash: <sha256>         # invalidates card when source changes
provider: {name, model}       # who generated it (provenance)

# ---- REQUIRED CORE (fixed) ----
purpose: <1–3 sentences>
modules:                      # key parts and their roles
  - {name, role}
dependencies:                 # internal + external
  - {name, kind: internal|external, why}
key_decisions:                # links into Decision Graph where known
  - {summary, decision_node_id?}
risks:
  - {description, severity: low|med|high}
recent_changes:               # from RepoIntel hotspots
  - {summary, ref}

# ---- OPTIONAL EXTENSIONS (project-defined, namespaced) ----
extensions:
  x_qa: {...}                 # e.g. test coverage notes
  x_security: {...}           # e.g. trust boundaries
  # arbitrary x_* blocks; validated only if a project registers a schema
```

### 9.2 Rules
- Core fields are validated by JSON Schema in `docs/schemas/`; unknown top-level keys rejected, but `extensions.x_*` is open.
- Cards are **invalidated by `source_hash` mismatch** → recompressed on next access (lazy) or via `forge compress`.
- Cards are graph nodes (`KnowledgeCard`), linked `summarized_by` to their targets.

---

## 10. Context Assembly Engine  *(NEW)*

The **request-time token-saver**. Given a task/query + a token budget, it builds the smallest sufficient context bundle.

### 10.1 Pipeline
```
1. Resolve intent → seed nodes (graph lookup, recent memory, task refs)
2. Expand → bounded graph traversal from seeds (depth/edge-type limited)
3. Gather → prefer knowledge cards > summaries > raw source (escalate only if needed)
4. Rank → relevance × salience × recency × hotspot
5. Budget → TokenIntel trims to fit; drops lowest-ranked first
6. Assemble → ordered, provenance-tagged context bundle + manifest
```

### 10.2 Principles
- **Cards before source.** Raw source is included only when a card is missing/insufficient and budget allows.
- **Deterministic & explainable.** The assembly manifest lists every included item, why it was chosen, and its token cost — auditable, no black-box selection.
- **Budget-aware.** Never exceeds the per-request token budget from §11; degrades gracefully (summaries → headlines → omit-with-note).

### 10.3 Output
A `ContextBundle {items[], manifest, total_tokens, dropped[]}` consumed by Orchestrator/providers.

---

## 11. Token Intelligence Engine  *(NEW)*

Answers **"How many tokens did we save, and are we within budget?"** — the measurement backbone for Principle 1.

### 11.1 Responsibilities
- **Counting:** estimate tokens for any text/bundle via `TokenizerPort`.
- **Budgets:** per-request / per-session / per-project budgets; enforce in Context Assembly.
- **Savings accounting:** compare *raw-equivalent* tokens (what naive context would cost) vs *assembled* tokens → records `tokens_saved` per request.
- **Reporting:** `forge tokens report` → savings over time, by project/provider/engine.

### 11.2 Tokenizer port (Open Question #6 — DECISION)
**Dual source, reconciled:** use **provider-reported usage** as the authoritative actual when available (Claude returns usage; Ollama returns eval counts); use a **local estimator** (tiktoken-style / heuristic) for *pre-flight* budgeting before the call. Store both; reconcile actual vs estimate to improve the estimator over time.

### 11.3 Data
```
token_events(id, request_id, scope_ref, provider, model,
             tokens_estimated, tokens_actual, tokens_raw_equiv,
             tokens_saved, created_at)
```

---

## 12. Decision Graph Design

Decision nodes = ADRs as graph citizens:
```yaml
type: Decision
props:
  title, status: proposed|accepted|superseded
  rationale, evidence: [source refs]
  alternatives: [...]
  approved_by, approved_at
edges: affects→Module/File, supersedes→Decision
```
Answers "**why was this implemented?**" via `forge why <module>` → traverses `affects` edges back to decisions. Mirrored as `docs/adr/NNNN-*.md` for human review.

---

## 13. Skill Graph Design

Skills = reusable, approved patterns (QA audit, arch review, debugging, security review, release readiness):
```yaml
type: Skill
props:
  name, intent, steps, inputs, outputs
  evidence_of_value, reuse_count
  status: proposed|approved|deprecated
  approved_by, approved_at
```
- Skills enter **only** through the Learning Engine + human approval.
- Stored in L2 (user) and/or L3 (project); orchestrator can invoke a skill as a structured plan.
- **V1 scope (ADR 0012): minimal** — Skill nodes created via approved Learning commit, plus
  `forge skill list|show`. **Lifecycle/versioning/deprecation/search/invocation → V2.**

---

## 14. Learning Engine Design

Strictly human-gated pipeline:
```
Observe (sessions, MemoryLifecycle) → Propose (structured) →
Human Review → Approve → Commit (snapshot + graph) → Become Skill/Memory
```
Every proposal MUST include: **evidence, benefits, risks, expected reuse value, token-savings estimate** (from §11). No autonomous promotion, no self-modification. Proposals live in `learning/proposals/*.yaml` until resolved.

---

## 15. Provider Layer & Provider Intelligence Tracking  *(tracking NEW)*

### 15.1 Provider Layer
Ports + adapters. V1: `claude`, `ollama` wired; `openai`, `gemini` stubs raising `NotImplemented` with clear messaging. Provider-specific code fully isolated; swapping touches only its adapter + config.

### 15.2 Provider Intelligence Tracking  *(NEW)*
Maintains a **scorecard per provider/model** so the Orchestrator can route intelligently and report cost/quality.

```
provider_stats(provider, model,
  calls, tokens_in, tokens_out, est_cost,
  avg_latency_ms, p95_latency_ms,
  success_rate, error_breakdown_json,
  last_seen_at, capabilities_json)   # context window, tools, modalities
```
- **Inputs:** every provider call emits a stats event (latency, tokens, success/error).
- **Use:** routing hints (cheapest-capable / fastest / most-reliable), budget forecasting, `forge provider stats`.
- **No autonomous switching** beyond configured routing policy; routing rules are explicit and human-set in V1.

---

## 16. Agent Orchestration & Parallel Execution Strategy  *(CLARIFIED)*

### 16.1 Agents
Architect, Engineer, QA, Reviewer, Security. Each: identifies assumptions, challenges weak logic, gathers evidence, proposes alternatives, assigns confidence. All findings carry evidence + provenance.

### 16.2 Parallel execution — DECISION (Open Question #4)
**Real concurrent provider calls via `asyncio`, bounded and observable** — not a fixtures-only stub.
```
Orchestrator:
  fan-out  → asyncio.gather over agent tasks
  bound    → asyncio.Semaphore (global + per-provider concurrency limits)
  protect  → per-call timeout, retry-with-backoff, per-provider rate limiting (from ProviderIntel)
  isolate  → one agent failure is captured as a finding, does not abort the run
  merge    → deterministic reducer: sort by (agent, severity, confidence), dedup, attach evidence
```
- **Determinism:** results are gathered concurrently but **merged in a stable, sorted order**, so output is reproducible regardless of completion timing.
- **Observability:** each agent run logs tokens (§11), latency, provider (§15), and its evidence trail.
- **V1 default concurrency:** global=5, per-provider configurable; Ollama defaults lower (local resource bound).

---

## 17. Adapter Design

Ports (abstract) + adapters (concrete). V1 ports: **StoragePort** (`sqlite` + YAML sync), **ProviderPort** (`claude`, `ollama`; `openai`/`gemini` stubs), **TransportPort** (`cli`; `mcp` is a **V2** seam — ADR 0012), **TokenizerPort** (provider-reported + local estimator), **VectorPort** (defined, unwired — V2 seam).

---

## 18. MCP Strategy

> Rule: **ForgeOS supports MCP; it does not require MCP.**

- ForgeOS **exposes** its own MCP server surfacing: Memory, KnowledgeGraph, Skill, Agent, Project services.
- MCP is one transport adapter over the same application services the CLI uses — **no logic lives in the transport.**
- If enterprise policy blocks MCP, the CLI adapter delivers full functionality.
- No dependency on external MCP servers; external integrations stay optional.
- **Scope (ADR 0012, 2026-06-21):** the **MCP adapter is deferred to V2**; ForgeOS **V1 is CLI-first**. The transport seam is preserved so MCP is purely additive later. When built (V2), MCP uses **stdio only** (local Claude Code / Desktop); socket/HTTP remains a later concern. *(Supersedes the earlier "stdio transport only in V1" decision / Open Question #5.)*

---

## 19. CLI Strategy

`forge` is the primary, always-available interface.
```
forge init                    # create <project>/.forgeos (L3); idempotent
# forge install removed from V1 — install via `uv tool install` / pip (ADR 0012)
forge scan                    # RepoIntel: ingest/refresh repo into graph
forge compress <path>         # produce/refresh knowledge card
forge memory add|query|gc     # gc = lifecycle pass
forge graph query|why <x>
forge context build <task>    # ContextAssembly preview + manifest
forge tokens report           # TokenIntel savings/budget report
forge learn review|approve|reject|commit   # human-gated learning (V1)
forge skill list|show         # minimal Skill capability (full Skill Graph → V2)
forge agent run <set>         # orchestrated multi-agent run
forge provider use <name> | stats
forge export|import|backup     # portability + backup
```
CLI is the V1 surface. A (future, **V2**) MCP adapter will call the same `services/`
layer; CLI↔MCP behavior parity is a **V2** test requirement (ADR 0012).

---

## 20. Knowledge Portability Strategy

- **Export:** `forge export` → versioned bundle (`forgeos-knowledge-vN.tar`) of all YAML/JSON snapshots + schema version, **excluding** the rebuildable SQLite.
- **Import:** `forge import` → validates schema version, rebuilds SQLite indexes.
- **Git-native:** L3 snapshots committed with the project; cloning the repo = inheriting its knowledge.
- **Schema versioning + migrations** keep old bundles loadable.

---

## 21. Storage Strategy

| Concern | Mechanism |
|---|---|
| Query/index | SQLite (per-scope DB files) — derived, rebuildable |
| Source of truth | YAML/JSON snapshots in git |
| Sync | write-through: mutations update SQLite + queue snapshot write |
| Location | L2 `~/.forgeos/`, L3 `<project>/.forgeos/` |
| Concurrency | single-writer service; CLI/MCP go through it |
| Integrity | schema validation on import; snapshot is canonical on conflict |

---

## 22. Backup Strategy  *(CLARIFIED — Open Question #7)*

**Two complementary layers; snapshots remain source of truth.**

1. **Primary — git-native (continuous):** L3 YAML/JSON snapshots are committed with the project. Normal version control = free, diffable, distributed backup with full history. This is sufficient for project knowledge.
2. **Secondary — explicit `forge backup` (point-in-time):** produces a timestamped, self-contained export bundle (same format as §20) to a configurable destination (default `~/.forgeos/backups/`), covering **L2 user knowledge** (which has no project git repo) and providing portable archives.

- **Retention:** configurable rolling retention (default: keep last N=10 bundles).
- **Scheduling:** **manual / git-driven by default; no built-in scheduler in V1.** Users may wire `forge backup` into their own cron/CI. (A managed scheduler is a V2/V3 concern.)
- **Restore:** `forge import <bundle>` rebuilds SQLite; round-trip tested.
- SQLite is never the backup unit — it is always reconstructable from snapshots/bundles.

---

## 23. Security Model

- **Local-first, least privilege:** no telemetry; no outbound calls except the selected provider.
- **Secrets:** provider API keys via env / OS keychain, never written to snapshots or git. `.forgeos/` ships a `.gitignore` excluding secrets + SQLite.
- **Provenance & auditability:** every learning/decision/lifecycle action records who/what/when.
- **No self-modification:** the system cannot promote skills, consolidate durable memory, or alter its own behavior without a human-approved commit.
- **Prompt-injection posture:** content pulled from repos/files is treated as data, not instructions, when assembling provider context (§10).

---

## 24. V1 Roadmap

Phased, each phase independently testable:

1. **Skeleton & ports** — repo, packaging, config loader, port interfaces (incl. TokenizerPort), fakes.
2. **Storage adapter** — SQLite + YAML snapshot sync + export/import/backup.
3. **Memory Engine + Lifecycle** — CRUD across scopes, graph links, TTL/decay/dedup, `forge memory gc`.
4. **Knowledge Graph** — nodes/edges, traversal, `forge graph query`.
5. **Repository Intelligence Engine** — scan, dep mapping, hotspots, incremental rescans, `forge scan`.
6. **Compression Engine** — knowledge cards (core schema + extensions), invalidation, `forge compress`.
7. **Token Intelligence Engine** — tokenizer adapters, budgets, savings accounting, `forge tokens report`.
8. **Context Assembly Engine** — seed→expand→rank→budget→assemble, manifest, `forge context build`.
9. **Decision + Skill graphs** — ADR/skill nodes, `forge why`.
10. **Provider layer + Provider Intelligence** — Claude + Ollama adapters, stats scorecards, stubs.
11. **Agent Orchestrator** — 5 agents, async bounded parallel run, deterministic merge.
12. **Learning Engine** — propose/review/approve/commit.
13. **Transport adapters** — **CLI complete (V1).** **MCP (stdio) + CLI↔MCP parity → V2 (ADR 0012).**
14. **Portability & backup hardening** — export/import/backup round-trip tests.

> **V1 scope reconciliation (ADR 0012):** the originally-listed V1 "MCP parity" and "full
> Skill Graph" are **deferred to V2**. V1 delivers **human-gated Learning (review/approve/
> reject/commit) + minimal Skill promotion** (Skill node via approved commit; `skill list|show`)
> over the **CLI**. See `docs/SCOPE-V1.md` / `docs/AMENDMENT-v1-scope.md`.

**Explicitly excluded (V1):** dashboard, voice, desktop app, hosted SaaS, GitHub app, enterprise governance, vector/embedding retrieval, scheduled backups, **MCP adapter + CLI↔MCP parity (→ V2, ADR 0012)**, **full Skill Graph lifecycle/versioning/search/invocation (→ V2)**, socket/HTTP MCP.

---

## 25. Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| SQLite ↔ snapshot divergence | High | Snapshot = source of truth; SQLite rebuildable; round-trip tests. |
| Token-savings claims unverified | Med | §11 measures raw-equiv vs assembled; reconcile estimate vs provider-reported actual. |
| Provider API drift (Claude/Ollama) | Med | Isolate in adapters; contract tests against recorded fixtures. |
| Graph-only retrieval insufficient | Med | VectorPort seam ready for V2 without core rewrite. |
| Context Assembly omits needed context | Med | Manifest + dropped[] visibility; escalate cards→source within budget; tune ranking. |
| RepoIntel mis-parses unusual languages | Low/Med | Heuristic fallback; incremental; never blocks — degrades to file-level nodes. |
| Memory lifecycle deletes useful memory | High | Archive-first (no hard delete on durable scopes); consolidation is human-approved. |
| Parallel agent runs overwhelm local Ollama | Med | Per-provider semaphore + rate limits from ProviderIntel; low Ollama default. |
| Scope creep into excluded V1 items | Med | Roadmap gate + ADRs; reject features failing token-efficiency test. |
| Secret leakage into snapshots/git | High | Keychain/env only; enforced `.gitignore`; import validation. |

---

## 26. Tradeoff Analysis

- **SQLite+YAML vs embedded graph DB:** portability + zero-dep simplicity over raw traversal speed. Revisit if traversal latency bites.
- **Graph-first vs vectors:** determinism + explainability + no embedding dependency; weaker fuzzy recall, deferred to V2.
- **Claude+Ollama both:** more upfront adapter work, but forces a genuinely provider-neutral abstraction (cloud + local) immediately.
- **Cards-before-source assembly:** maximal token savings + auditability; risk of under-context, mitigated by manifest visibility and budget-aware escalation.
- **Dual tokenizer (estimate + actual):** more bookkeeping, but yields trustworthy savings numbers and a self-improving estimator.
- **Real async parallelism with deterministic merge:** more engineering than a stub, but proves orchestration for real and stays reproducible.
- **Archive-first lifecycle:** uses more disk, but makes memory management safe and reversible.
- **CLI + MCP parity:** doubles transport testing but guarantees ForgeOS survives MCP being policy-blocked.
- **Human-gated learning:** slower knowledge accrual vs safety/auditability — chosen per Principle 2.

---

## 27. Open Questions

Resolved in Rev 2: **#4 (parallel exec → async bounded), #5 (MCP → stdio-only)** — *MCP **timing** superseded by ADR 0012: the MCP adapter is **deferred to V2** (stdio remains the chosen design when built)* — **#6 (tokenizer → dual source), #7 (backup → git + manual `forge backup`).**

Still open:
1. **Repo location:** keep at `~/code/forgeos` (sandbox blocked `Documents/GitHub`) or relocate later?
2. **Python version & tooling:** target 3.11 or 3.12? Toolchain (uv / poetry / pip), linter (ruff), test runner (pytest)?
3. **Compression generation cost:** cards require provider calls — generate on-demand (lazy) only, or also a bulk `forge compress` pass at scan time? (Leaning lazy + opt-in bulk.)
4. **RepoIntel language scope for V1:** which languages get first-class parsers (e.g. Python + JS/TS) vs heuristic fallback for the rest?
5. **Provider cost data:** hardcode a pricing table for cost estimates, or require users to supply per-model pricing in config?

---

## Next step
Awaiting **approval of Rev 2 additions + answers to remaining open questions** (esp. #2 tooling). On approval I produce the detailed implementation **Plan** (still no code) for the second approval gate.
