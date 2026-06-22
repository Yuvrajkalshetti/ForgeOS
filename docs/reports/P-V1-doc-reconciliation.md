# Documentation Reconciliation Report — D1 (agent naming) + C1 (MCP scope)

- **Date:** 2026-06-22 · **Status:** ✅ complete, STOP for approval.
- **Scope:** documentation only — no code, no behavior, no tests changed. Applies
  **already-approved** decisions (ADR 0012 / `AMENDMENT-v1-scope.md`); no new scope decided.

## Method
Audited all architecture docs, ADRs, amendments, plans, handoff, reports, README, and
`pyproject.toml`. Code is authoritative for D1: the execution-agent set is defined in
`src/forgeos/core/orchestrator/agents.py` = **Architect, Engineer, QA, Reviewer, Security**.

## Contradictions Found
**D1 — execution-agent naming** (two docs used an obsolete set
"Planner/Researcher/Coder/Reviewer/Tester" that never matched the code):
- `docs/adr/0010-advisory-system.md:9`
- `docs/AMENDMENT-advisory-system.md:18`
(ARCHITECTURE §3/§16 and IMPLEMENTATION_PLAN §6.3/§9 were already correct.)

**C1 — MCP / Skill-Graph scope** (docs still placed MCP and a full Skill Graph in V1,
contradicting ADR 0012 / AMENDMENT-v1-scope):
- `ARCHITECTURE.md`: §3 component table (Transport = "CLI + MCP"; Skill Graph unscoped),
  §13 Skill Graph, §17 TransportPort, §18 MCP Strategy ("stdio in V1"), §19 CLI (listed
  removed `forge install`; `skill list|propose|approve`; "CLI and MCP both…parity"),
  §24 roadmap item 13 + exclusions, §27 Open Question #5.
- `IMPLEMENTATION_PLAN.md`: approved-decisions ("MCP stdio only for V1"), §1 phase table P7,
  §2 WBS 7.3/7.4, §7 CLI table (`forge install`, `skill list|propose|approve`), §8 MCP
  Service Design (whole section V1), §14 acceptance criterion **A10** (MCP/parity as a V1 AC),
  §15 build order.
- `docs/adr/0007-mcp-stdio-only-v1.md`: title + body asserted MCP "in V1".
- `docs/AMENDMENT-advisory-system.md`: roadmap row P7 "(incl. … MCP)"; §7 P7-impact MCP/parity note.

**No drift found in:** README.md, pyproject.toml, SCOPE-V1.md, AMENDMENT-v1-scope.md,
ADR 0012, AUDIT-mcp-skill.md, RELEASE-CHECKLIST-v1.md, reports/ (already consistent).

## Contradictions Resolved
**D1:** unified both occurrences to **Architect / Engineer / QA / Reviewer / Security**;
added a one-line authoritative statement to the ARCHITECTURE banner. Single authoritative set.

**C1:** applied ADR 0012 consistently — everywhere now reflects:
**V1 = CLI-first · MCP adapter + CLI↔MCP parity = V2 · Full Skill Graph = V2 · Minimal Skill Promotion = V1.**
- ARCHITECTURE.md: added a locked-scope reconciliation banner; annotated §3/§13/§17/§18/§19/
  §24/§27; removed `forge install` and corrected CLI to `forge learn …` + `forge skill list|show`;
  moved MCP + full Skill Graph into V1 exclusions (→ V2).
- IMPLEMENTATION_PLAN.md: added banner; P7 row + WBS marked MCP→V2; CLI table fixed; §8 headed
  **DEFERRED TO V2**; **A10 reclassified as a V2 (non-V1) criterion**; build order annotated.
- ADR 0007: status "timing amended by ADR 0012"; title + decision note MCP deferred to V2
  (stdio remains the design when built; seam preserved).
- AMENDMENT-advisory-system.md: P7 roadmap row + P7-impact note mark MCP/parity → V2.

## Files Modified (and why)
| File | Change | Reason |
|---|---|---|
| `docs/adr/0010-advisory-system.md` | agent set → Architect/Engineer/QA/Reviewer/Security | D1 |
| `docs/AMENDMENT-advisory-system.md` | agent set (line 18); P7 row + P7-impact MCP→V2 | D1 + C1 |
| `docs/adr/0007-mcp-stdio-only-v1.md` | title + status/decision: MCP deferred to V2 (ADR 0012) | C1 |
| `docs/ARCHITECTURE.md` | scope banner + §3/§13/§17/§18/§19/§24/§27 edits; CLI fixes | C1 (+D1 banner) |
| `docs/IMPLEMENTATION_PLAN.md` | banner + phase/WBS/CLI/§8/A10/build-order edits | C1 |
| `docs/HANDOFF.md` | mark doc-reconciliation done; remaining-work updated | bookkeeping |

## Constraints Honored
Documentation only; no code; no behavior change; **no test changes** (no doc-validation
tests exist); no new architecture features; no new scope decisions; only applied approved
ADR 0012. Synced-in-`$TMPDIR` docs (ADR 0007/0010, advisory amendment) were edited in the
dev tree and synced to `~/code` so a future code-phase sync cannot clobber them.

## Remaining V1 Work After Reconciliation
**V1 Build-Complete surface: none remaining.** All build deliverables (P0–P6.6, Learning
review/approve/reject/commit + provenance, minimal Skill promotion, `forge learn`/`skill`/
`export`/`import`/`backup`/`init`, doc reconciliation) are implemented and green (235 tests).
What remains is **release-gate validation only** (outside the sandbox; not a build deliverable):
real Claude smoke · real Ollama smoke · actual-vs-estimated token reconciliation · release
checklist. *(Not started — awaiting explicit approval.)*

## Confidence
**High.** Drift was localized and fully enumerated by tree-wide grep; verified zero
obsolete agent names remain and ADR-0012 scope is now stated consistently (with a precedence
banner where older prose survives).
