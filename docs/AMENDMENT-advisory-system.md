# Architecture Amendment — Advisory System

> Status: **Approved (amendment); awaiting approval to implement as P6.5.** No code yet.
> Companion: ADR 0010. Sequencing: after P6 (done), before P7.

This amendment introduces an **Advisory System** (Mentor + Auditor) that is wholly
separate from the **Execution System** (Orchestrator + execution agents, P6). The
Advisory System never executes, implements, deploys, merges, or approves. Final
approval authority always remains human.

---

## 1. Architecture document update

```
ForgeOS
├── Execution System            (builds things — existing)
│   ├── Architect / Engineer / QA / Reviewer / Security
│   └── Orchestrator            (core/orchestrator, P6)
└── Advisory System             (NEW — core/advisory, P6.5)
    ├── Mentor                  (works BEFORE execution: strategy, challenge, plan)
    └── Auditor                 (works AFTER plan/impl: evidence, compliance, claims)
```

- **Mentor** — provider-backed reasoning agent. Produces the required structured
  output (`Understanding / Assumptions / Challenges / Gaps / Alternatives /
  Recommendation / Proposed Plan / Confidence`). Every response begins with
  `Your proposal:` / `Your question:` / `Your request:`. Never executes/approves.
- **Auditor** — provider-backed, skeptical-by-default. Produces (`Scope / Evidence
  Review / Architecture Compliance / Test Coverage / Risks / Violations /
  Recommendation / Confidence`). Findings must be traceable to evidence; missing
  evidence is explicitly flagged. Never executes/approves.

**Boundary rules (enforced):** neither agent can execute, deploy, merge, approve,
or override human decisions. Advisory ↔ Execution import isolation is verified by a
static guard test. Advisory may *read* graph/repo context and *write* advisory
nodes only.

---

## 2. Repository structure update

```
src/forgeos/core/advisory/          # NEW subsystem (NOT under orchestrator/)
    __init__.py
    models.py        # MentorRecommendation, AuditFinding (+ output sections)
    mentor.py        # Mentor (provider-backed; structured strategy output)
    auditor.py       # Auditor (provider-backed; evidence-based findings)
src/forgeos/adapters/transport/cli/
    mentor.py        # `forge mentor` (NEW)
    audit.py         # `forge audit`  (NEW)
```
No change to `core/orchestrator/`. Advisory persists artifacts via the existing
graph (`nodes`/`edges` collections) — no new storage collection required.

---

## 3. Knowledge graph design update

**New node types:** `MentorRecommendation` ("MentorRecommendation"), `AuditFinding`
("AuditFinding").

**New edge types** (added to the typed registry):
| Edge | Src | Dst | Meaning |
|---|---|---|---|
| `advises` | MentorRecommendation | File, Module, Project, Decision | recommendation targets a subject |
| `informs` | MentorRecommendation | Decision | recommendation fed a human decision |
| `audits` | AuditFinding | File, Module, Project, Decision | finding evaluates a subject |

**Traceability chain** (the amendment's required lineage):
```
MentorRecommendation --informs--> Decision(human) --affects--> File/Module <--audits-- AuditFinding
```
`Decision` (existing node type) represents the **human decision**; its `approved_by`
/ `approved_at` props record human authority. Implementation = existing File/Module
nodes from RepoIntel. This makes the full lineage queryable (e.g., `forge graph
query <decision>` or a future `forge why`-style trace).

---

## 4. Memory model update

**Low impact (additive, no schema change).** Advisory artifacts are first-class
**graph nodes**, not new memory records, so `MemoryRecord` is unchanged. Memory may
reference advisory nodes through its existing `links: [node_ids]` field (e.g., a
session note linking the Mentor recommendation it acted on). No new `MemoryKind` is
required. Advisory nodes carry their own provenance (`provider`, `generated_at`).

---

## 5. Learning model update

The advisory lineage becomes a **learning signal** (human-approved only, unchanged):

- The Learning Engine may observe completed chains
  (`MentorRecommendation → Decision → Implementation → AuditFinding`) and **propose**
  skills/patterns — e.g., "recommendations of type X that were accepted and later
  passed audit" → a reusable advisory pattern.
- New proposal kinds (additive): `advisory.pattern`, `audit.recurring_violation`.
- **No autonomous promotion.** Advisory never approves or commits learnings; it only
  emits recommendation/finding nodes and (optionally) learning *proposals*. Promotion
  remains the human-gated pipeline (P7/P12).

---

## 6. Roadmap update

Insert **P6.5 — Advisory System** between P6 and P7. V1 scope now includes the
Advisory System. Exclusions (dashboard, vector, hosted, voice, etc.) unchanged.

| Phase | Name | Status |
|---|---|---|
| P6 | Providers + Orchestrator (Execution) | ✅ done |
| **P6.5** | **Advisory System (Mentor + Auditor)** | **proposed (this amendment)** |
| P7 | Learning + Transports (advisory-aware learning; **MCP → V2 per ADR 0012**) | reconciled — see `docs/SCOPE-V1.md` |

---

## 7. Implementation plan impact assessment

**New work (P6.5):**
- `core/advisory/models.py` — `MentorRecommendation`, `AuditFinding` pydantic models
  mirroring the required output sections; helpers to persist them as graph nodes.
- `core/advisory/mentor.py` — Mentor: builds a context-grounded prompt (graph/repo
  profile + user input), calls `ProviderPort`, parses into the structured output,
  writes a `MentorRecommendation` node (+ `advises`/`informs` edges).
- `core/advisory/auditor.py` — Auditor: gathers evidence (acceptance criteria, tests,
  graph/profile, diffs if provided), calls provider, parses findings, writes an
  `AuditFinding` node (+ `audits` edges); explicitly marks missing evidence.
- `core/graph/models.py` + `registry.py` — **additive** NodeType/EdgeType + rules.
- `adapters/transport/cli/{mentor,audit}.py` — `forge mentor`, `forge audit`
  (provider-backed; graceful when no provider, like `agent run`).
- Tests: mentor/auditor output-structure + node/edge emission (FakeProvider),
  advisory↔execution import-isolation guard, "advisory cannot approve" guard,
  graph registry rules, CLI graceful-without-provider + success (injected provider).

**Reused (no new infra):** ProviderPort + MeteredProvider (P6), GraphStore (P3),
StatsRecorder/Router (P6), config/observability (P0). Estimated size: comparable to
the orchestrator slice of P6; **Medium** complexity.

**Dependencies satisfied:** providers (P6 ✅), graph (P3 ✅), context (P5 ✅).

**P7 impact:** P7's Learning gains advisory-aware proposal kinds. *(MCP note superseded by
ADR 0012: the MCP transport — including exposing advisory `mentor`/`audit` services for
CLI↔MCP parity — is **deferred to V2**. In V1 the CLI surfaces advisory services.)*

---

## 8. Migration impact

**Backward compatible; additive only.**
- **Graph enums:** new NodeType/EdgeType values added; no values removed or renamed.
  Existing `nodes.yaml`/`edges.yaml` snapshots load unchanged.
- **Storage:** generic record store (ADR 0008) — **no `schema_version` bump**, no new
  collection, no migration script. Advisory nodes live in the existing `nodes`/`edges`.
- **Card / memory / token schemas:** unchanged.
- **Existing tests (174):** unaffected; no behavioral change to P0–P6 code paths
  except additive edits to `graph/models.py` and `graph/registry.py`.
- **Rollback:** removing the advisory package and the additive enum/registry entries
  restores the prior state; any persisted advisory nodes would simply be unknown
  types (gracefully ignorable) — but no rollback is anticipated.
- **Provider isolation preserved:** advisory is provider-backed but optional; all
  provider-free engines and no-provider operation are unchanged.

---

## 9. Risks
- **Boundary erosion** (advisory drifting into execution/approval) — mitigated by
  import-isolation guard + "no approval path" guard tests.
- **Provider dependence** for advisory output — mitigated by graceful no-provider
  behavior; advisory is optional and never blocks core/execution.
- **Parsing structured LLM output** (as in P6) — mitigated by schema validation and
  failure isolation.

## 10. Confidence
**High** for the design (small, additive, mirrors the proven P6 provider/agent
pattern; clear separation and migration story). The only inherent uncertainty is the
quality/parse-robustness of provider output, already handled the same way as the
Execution agents.

---

## Approval gate
Awaiting explicit human approval to implement **P6.5 — Advisory System**. On
approval, implementation proceeds under the standard contract (TDD, ruff/mypy/pytest
gates, structured report) and **then** P7 begins.
