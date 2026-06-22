# P6.6 — Advisory Intelligence Wiring (Plan — awaiting approval)

> Status: **plan only; no implementation.** Converts Mentor/Auditor from
> prompt→LLM→response into ForgeOS-grounded advisors by feeding them a budgeted
> ContextBundle assembled from existing components. Reuses Context Assembly + Token
> Intelligence. No new storage/graph/provider, no vectors/embeddings/semantic.

## Objective
Before Learning (P7), make Mentor and Auditor *use the knowledge ForgeOS already
has*. Mentor and Auditor receive a deterministic, token-budgeted `ContextBundle`
(grounding) built only from existing sources; the bundle text becomes the grounded
context for the provider call, and its manifest is recorded for auditability.

## Grounding sources (all existing; read-only)
- **Mentor:** Knowledge Cards · Memory (project+user) · ADRs (`docs/adr/*.md`) ·
  Repo Profile · related Decisions · past Audit Findings.
- **Auditor:** Acceptance Criteria (caller-provided text) · related Decisions ·
  past Audit Findings · relevant Cards · Available Evidence (caller-provided text).

Mapping to current stores (no new systems):
| Source | Where it already lives | Access (existing) |
|---|---|---|
| Knowledge Cards | `cards` collection + `KnowledgeCard` nodes | ContextAssembler (cards-first) |
| Memory | `memory` collection | `MemoryService.query` (P2) |
| ADRs | `docs/adr/*.md` files | filesystem read (same pattern as `source_root`) |
| Repo Profile | `repo_profile` record | `store.get(REPO_PROFILE)` (P4) |
| Decisions | `Decision` nodes | `GraphStore` (P3) |
| Past Audit Findings | `AuditFinding` nodes (P6.5) | `GraphStore.nodes(AUDIT_FINDING)` |
| Acceptance Criteria / Evidence | caller input | passed as text → wrapped as items |

## 1. Architecture impact assessment
- **New (additive, core, provider-free):** `core/advisory/context.py` —
  `AdvisoryContextBuilder` composing existing components into one `ContextBundle`.
  It imports only core (`ContextAssembler`, `MemoryService`, `GraphStore`,
  `TokenLedger`) + ports (`TokenizerPort`, `StoragePort`); **no adapters, no provider**.
- **Refactor (additive, low-risk):** extract the rank→budget→manifest→ledger tail of
  `ContextAssembler.build` into a reusable `assemble(items, scope_ref)` so the builder
  feeds arbitrary `ContextItem`s through the *same* budgeting. `build()` keeps its
  current behavior (existing P5 tests unchanged).
- **Mentor/Auditor change:** accept an optional `grounding: ContextBundle`; when
  present, prepend its rendered text to the provider prompt and store the manifest
  refs in the recommendation/finding node `props` (traceability). Default `None`
  preserves current behavior.
- **CLI:** `forge mentor` / `forge audit` build grounding via the builder and pass it
  in. New flags: `--depth`, `--budget`, `--adr-dir`, `--criteria`, `--evidence`,
  `--no-ground`.
- **Token Intelligence:** reused — the builder records one grounding token event
  (raw-equivalent vs assembled) so `forge tokens report` shows advisory savings.
- **Boundaries unchanged:** advisory stays separate from execution; the builder is
  provider-free; Mentor/Auditor remain the only provider callers (allowed, ADR 0010).
- **No changes to:** storage schema, graph node/edge types, provider abstractions,
  memory model, learning model. ADR **0011** to be recorded ("advisory grounding via
  Context Assembly").

## 2. Implementation plan (build order, TDD)
1. **Refactor ContextAssembler** — extract `assemble(items, scope_ref)`; `build()`
   delegates to it. Regression: all P5 assembler tests stay green.
2. **AdvisoryContextBuilder** — source collectors → `list[ContextItem]`:
   cards/decisions/findings (graph, deterministic queries, recent-N), memory
   (`MemoryService.query`, salience/recency sort), repo profile (record→summary item),
   ADRs (file read, title+Decision section), caller criteria/evidence (text items).
   Deterministic **kind-weight ranking**: card 3.0 · decision 2.5 · finding 2.5 ·
   adr 2.0 · repo_profile 2.0 · memory 1.5 · criteria/evidence 2.0 · source 1.0 ·
   stub 1.0 (tiebreak: score desc, then ref). Feed through shared `assemble`.
   Two entrypoints: `for_mentor(focus, …)`, `for_auditor(scope, criteria, evidence, …)`.
3. **Mentor/Auditor** — add `grounding: ContextBundle | None`; render into prompt;
   persist `grounding_refs` in node props.
4. **CLI wiring** — build grounding in `mentor`/`audit` commands; flags above;
   `--no-ground` bypasses (keeps current behavior).
5. **Tests** (below).
6. **Gates** (`scripts/check.py` + pytest) green; sync; report; **stop**.

## 3. Risk assessment
| Risk | Severity | Mitigation |
|---|---|---|
| Grounding blows the token budget | Med | Reuse Context Assembly budget + manifest drops; default `--budget` from config `tokens.per_request` |
| Non-determinism (memory/file ordering) | Med | Deterministic sorts everywhere; fixed kind-weights; clock-injected |
| Over-coupling Mentor→builder | Low | Mentor takes a `ContextBundle`, not the builder; builder injected at CLI |
| Missing sources (no ADRs/memory/profile) | Low | Each collector is optional and skips gracefully; advisors still run |
| Stale cards grounding advice | Low | Existing `source_hash` invalidation (P5) |
| Scope creep toward retrieval/vectors | Med | Explicit constraint; graph + structured queries only; guard test asserts no embeddings deps |
| Regression in ContextAssembler refactor | Med | `build()` behavior preserved; full P5 suite must stay green |
| Cost of grounding > benefit on tiny repos | Low | Token event records net savings; `--no-ground` escape hatch |

## 4. Acceptance criteria
- **AC1** Mentor grounding bundle includes items from cards, memory, ADRs, repo
  profile, decisions, and past findings (when present); manifest lists each with
  kind, tokens, score, and include/drop reason.
- **AC2** Auditor grounding bundle includes acceptance criteria, decisions, past
  findings, relevant cards, and evidence (when present).
- **AC3** Grounding respects the token budget (`total_tokens <= budget`) and is
  **deterministic** (same repo+inputs+budget → identical bundle).
- **AC4** A grounding **token event** is recorded (raw-equivalent vs assembled →
  savings) via the existing `TokenLedger`; visible in `forge tokens report`.
- **AC5** The provider prompt actually contains the grounding (test asserts grounded
  text reached the provider via a fake).
- **AC6** No new storage/graph/provider abstractions; no vector/embeddings/semantic
  imports (structural/guard test).
- **AC7** `AdvisoryContextBuilder` is provider-free; all P6.5 advisory boundary tests
  still pass.
- **AC8** Recommendation/Finding nodes persist `grounding_refs` (the manifest item
  refs) for lineage/traceability.
- **AC9** Advisors run gracefully with empty sources (no cards/memory/ADRs).
- **AC10** No regression: all prior tests (193) remain green.

## Approval gate
Awaiting human approval to implement P6.6. On approval: TDD per the build order,
ruff/mypy(substitute)+pytest gates, structured report, then **stop** (still no P7).
