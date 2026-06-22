# ForgeOS — V1 Completion Review (Mentor+Auditor) & P7 Plan

Evidence-based; repository re-inspected. No implementation. Stop after delivery.

## Audit Validation (each claimed blocker)
| Blocker | Status | Evidence | True V1 blocker? |
|---|---|---|---|
| Learning approve/review/commit | **Confirmed missing** | `core/learning/proposal.py` exposes only `emit_proposal`/`list_proposals`; no `approve/commit/review`. BUT `LearningProposal` already has evidence/benefits/risks/reuse_value/token_savings_est/status fields. | **Yes** — the human gate is the Learning Engine's purpose; only the substrate exists. |
| MCP stdio adapter | **Confirmed missing** | `adapters/transport/` contains only `cli/`. | **Disputed** — ADR 0007 + architecture principle "supports MCP; does **not require** MCP; CLI delivers full functionality." MCP is listed in V1 scope but explicitly optional. Strong V2 candidate. |
| CLI↔MCP parity | Missing (depends on MCP) | no MCP server exists | Only if MCP stays in V1. |
| Skill Graph service | **Confirmed missing** | no `core/skill/`; only `NodeType.SKILL` + `uses_skill` rule. | **Partial** — coupled to Learning ("skills evolve via approved learning"). Weak value without Learning commit. |
| `forge install` | Confirmed absent | no command registered | **No** — installation is `uv tool install`/pip, not a code feature. **Remove from V1.** |
| `forge init` | Confirmed absent | `open_store` auto-creates `.forgeos` | **Weak** — convenience only; small or defer. |
| `forge export/import/backup` | **Confirmed (CLI) absent; services exist+tested** | `services/portability.py` has all three; `test_portability` green; no CLI ref. | **Yes (small)** — finishing task, not new design. |
| Live provider smoke | Confirmed unverified | adapters tested via `httpx.MockTransport` only | **Reclassify** — release gate run outside sandbox, not build work. |
| Doc drift (Execution agents) | **Confirmed** | impl `architect/engineer/qa/reviewer/security`; amendment said `Planner/Researcher/Coder/Reviewer/Tester` | **Yes (doc-only)**. |

**Audit verdict:** mostly correct, but over-states three items — `forge install` (not a feature), MCP (architecturally optional), live-smoke (a gate, not code). Portability is a small wiring task, not a deep blocker. The audit *under-stated* one thing: **Learning→Skill promotion** ("Become Skill") is the missing bridge tying Learning to the Skill Graph; treat them as one workstream.

## Missing Requirements (not in the audit)
- **Learning→Skill promotion** ("Observe→Propose→Approve→Commit→Become Skill") — the commit step should *create Skill nodes*; this links blockers B1+B3.
- **Audit trail / provenance for approvals** — who approved a proposal/decision (proposal has no `approved_by`); minor.
- **Advisory→Learning feedback** (recurring findings → proposals) — already slated P7; keep.

## Architecture Drift / Contradictions
- **D1 (confirmed):** Execution-agent names differ between original Architecture §Agent System (implemented) and the Advisory amendment's Execution System list. Doc-only reconciliation.
- **C1 (contradiction):** Architecture lists "MCP Adapter" in V1 scope *and* states ForgeOS "does not require MCP" with CLI sufficient. Must be resolved by a scope decision (keep stdio MCP vs defer to V2).
- No undocumented code drift. ADR 0009 (provider-free compression) and ADR 0011 (tiers) are documented supersessions, not drift.

## Advisory System Review (challenged)
- **Mentor — useful, with a real limitation.** Grounds via ContextBundle (cards/memory/ADRs/profile/decisions/findings). Strong for "advise about existing code X"; **weak for greenfield** ("add feature Y" has no focus node → grounding thins to repo_profile + recent items). Honest gap, not a blocker.
- **Auditor — useful but shallow on evidence.** It consumes only **caller-provided** criteria/evidence text + graph items; it does **not** auto-harvest test results or acceptance-criteria docs. "Evidence-based" is only as good as what's pasted. V1-acceptable; enhancement later.
- **Grounding — sufficient.** Deterministic tiers + budget + manifest + recorded savings; AC11 enforced. Good enough for V1.
- **AdvisorySession — minimal/manual.** Lineage is hand-attached (mentor starts a session; audit attaches by id); no automatic cross-command linking of decision/implementation. Sufficient as bookkeeping; not yet an automated lineage. Not a blocker.
- **Advisory→Learning — keep in P7.** Correct sequencing.
- **Verdict:** Advisory is functionally complete and boundary-safe; its weaknesses are enhancements, **not V1 blockers.** Do not block V1 on advisory depth.

## V1 Recommendation (A / B / C)
**A — Complete V1 exactly as planned** (Learning + MCP + Skill + all CLI + live).
- Benefits: matches literal original scope. Risks: longest path; builds MCP/Skill of uncertain near-term value. Complexity: **High**.

**B — Reduce scope; CLI-first V1, defer MCP + full Skill Graph to V2.** *(Recommended)*
- V1 = Learning approve/commit **with minimal Skill promotion** + portability CLI + `forge init` + doc reconciliation + live-provider smoke (release gate). Defer the standalone **MCP adapter/parity** and a **full Skill Graph service** to V2, justified by ADR 0007 / "does not require MCP," and by Skill value depending on accrued learnings.
- Benefits: fastest credible V1; fully delivers the token-efficiency core on the guaranteed CLI surface; lowest risk. Risks: requires stakeholder sign-off to defer two listed items; weaker "skills" story at V1. Complexity: **Low–Med**.

**C — Add work before V1** (advisory auto-evidence/auto-lineage, greenfield grounding).
- Benefits: stronger advisory. Risks: scope creep, delays V1 for non-essential polish. Complexity: **Med–High**. **Not recommended.**

**Recommendation: B.** It ships the actual value proposition soonest and honors the architecture's own "CLI is sufficient" principle. If MCP/Skill are non-negotiable for the V1 label, fall back to **A** but sequence MCP/Skill last. Reject C for V1.

## P7 Implementation Plan (detailed; no code)
Order chosen so each item is independently shippable; doc fix first (free), value-core next, optional/heavy last.

### P7.0 Documentation reconciliation (D1, C1)
- **Objective:** one source of truth for Execution agent names; resolve MCP scope.
- **Arch impact:** docs only. **Deps:** none.
- **AC:** Architecture + amendment agree on agent names; an ADR records the MCP V1-vs-V2 decision.
- **Tests:** none (doc). **Risks:** none. **Build:** first.

### P7.1 Learning Engine — approve/review/commit + Skill promotion (B1, +bridge to B3)
- **Objective:** human-gated `review → approve|reject → commit`; commit may **create a Skill node**.
- **Arch impact:** extend `core/learning` (new `pipeline.py`: `review/approve/reject/commit`); commit writes graph nodes (Skill) and/or applies a memory consolidation; provenance `approved_by/at`. No new storage.
- **Deps:** Learning proposals (done), Graph (done), Memory (done).
- **AC:** approve transitions status proposed→approved with provenance; commit materializes the approved artifact (e.g., Skill node) **only** on human action; reject closes; nothing auto-promotes; full lineage queryable.
- **Tests:** approve/reject/commit transitions; "no auto-promotion" guard; commit creates Skill node; idempotent commit; CLI `forge learn list|show|approve|reject|commit`.
- **Risks:** scope of "commit" (skill vs memory vs decision) — keep to Skill + memory consolidation for V1. **Build:** second.

### P7.2 Skill Graph (B3) — minimal
- **Objective:** approved skills as first-class, queryable nodes (created via P7.1 commit).
- **Arch impact:** `core/skill/` service (CRUD/list/get over `Skill` nodes; `uses_skill` edges already in registry). No new storage/graph types.
- **Deps:** P7.1 (skills enter only via approved learning), Graph.
- **AC:** skills created only through approved commit; `forge skill list|show`; skill carries intent/steps/status/approved_by.
- **Tests:** skill created via commit; skills not creatable ad-hoc without approval; list/get; snapshot round-trip.
- **Risks:** thin value without many learnings — acceptable for V1-minimal. **Build:** third (or defer to V2 under Option B).

### P7.3 CLI completion (B4, minus install)
- **Objective:** wire existing services to CLI: `forge export|import|backup`; add `forge init`. **Drop `forge install`** (document `uv tool install`).
- **Arch impact:** new CLI modules calling `services/portability.py`; `init` scaffolds `.forgeos`. No core changes.
- **Deps:** portability service (done).
- **AC:** `export`→`import` round-trips via CLI; `backup` writes + prunes; `init` creates `.forgeos`; help lists them.
- **Tests:** CLI round-trip (mirrors `test_portability`); `init` idempotent.
- **Risks:** trivial. **Build:** fourth.

### P7.4 MCP Adapter (stdio) (B2) — *Option A only; else V2*
- **Objective:** expose Memory/Graph/Skill/Agent/Project + advisory over MCP stdio, as a transport over the same services.
- **Arch impact:** `adapters/transport/mcp/`; no business logic in transport. Needs an MCP server lib (dependency — currently none; offline-install blocked here).
- **Deps:** services layer; P7.1–7.3 for full surface.
- **AC:** each MCP tool maps to a CLI-equivalent service call; stdio server starts/responds.
- **Tests:** tool-handler unit tests; see P7.5.
- **Risks:** **new dependency** (MCP SDK) — uninstallable in this sandbox (network); CI/real-env only. **Build:** fifth.

### P7.5 CLI↔MCP parity
- **Objective:** prove identical results via both transports.
- **Arch impact:** shared service layer (already the design).
- **Deps:** P7.4.
- **AC:** a parity table asserts CLI result == MCP result for each operation.
- **Tests:** parity suite over the common services.
- **Risks:** drift if a transport bypasses services. **Build:** sixth.

### P7.6 Live provider verification (B5) — release gate
- **Objective:** smoke-test Claude + Ollama against real endpoints.
- **Arch impact:** none (adapters done).
- **Deps:** network + API key / local Ollama (outside this sandbox).
- **AC:** one real generate per provider returns text + usage; recorded by stats/ledger.
- **Tests:** opt-in, key-gated integration test (skipped without creds).
- **Risks:** environment; **not a code blocker.** **Build:** last (gate).

## Risks (cross-cutting)
- Deferring MCP/Skill (Option B) needs explicit stakeholder acceptance vs the literal V1 list.
- New MCP dependency cannot be installed/verified in the current sandbox.
- Learning "commit" scope can balloon — constrain to Skill + memory consolidation.
- Advisory limitations (greenfield grounding, auto-evidence) remain post-V1 enhancements.

## Confidence
**High** on the audit validation and drift findings (all repository-verified). **Medium-High** on the recommendation (B), pending the stakeholder scope decision on MCP/Skill. **Medium** on MCP effort estimate (unverified dependency in this environment).
