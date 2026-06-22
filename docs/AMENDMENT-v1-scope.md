# Architecture Amendment — V1 Scope Decision (MCP & Skill Graph)

> Status: **APPROVED (2026-06-21).** Companion: ADR 0012. MCP + full Skill Graph → V2.
> Approved with a two-tier completion model (see "V1 Completion Milestones" below).

## V1 Completion Milestones (approved clarification)

**V1 Build Complete** — code + tests, achievable under the standard gates:
- P0–P6.6 (done)
- Learning review/approve/reject/commit
- Minimal Skill promotion (Skill node via approved commit; `forge skill list|show`)
- Portability CLI (`export`/`import`/`backup`)
- `forge init`
- Documentation reconciliation (D1 agent names, C1 MCP scope)

**V1 Release Ready** — gates beyond the build (mostly outside this sandbox):
- Live provider smoke (real Claude + Ollama calls)
- Real token reconciliation verification (estimate vs provider-reported actual)
- Release checklist pass (see `docs/RELEASE-CHECKLIST-v1.md`)

MCP and the full Skill Graph remain **V2**.


## Evaluation 1 — Should MCP remain in V1?
**Facts (repo/docs):** MCP is listed in the Architecture "V1 Scope," yet the same
Architecture states the principle *"ForgeOS supports MCP. ForgeOS does not require
MCP,"* and **ADR 0007** says *"the CLI delivers full functionality if MCP is
unavailable."* No MCP code exists; `adapters/transport/` contains only `cli/`. MCP
needs a new SDK dependency (uninstallable/unverifiable in the current environment).

**Assessment:** MCP is an *integration convenience* (Claude Desktop/Code), not part
of the token-efficiency value proposition. Every capability (memory, graph,
compression, context assembly, token intelligence, providers, advisory) is fully
usable via the guaranteed CLI surface. Building MCP now spends real effort + adds an
unverifiable dependency for zero core-value gain in the first usable release.

**Decision: DEFER MCP to V2.** Keep the transport-adapter seam (services layer is
already transport-agnostic), so MCP is purely additive later.

## Evaluation 2 — Should a full Skill Graph remain in V1?
**Facts:** "Skill Graph" is listed in V1 scope; the Architecture says *skills evolve
only through approved learning.* Today only `NodeType.SKILL` + the `uses_skill` edge
rule exist; there is no skill service. The Learning approve/commit pipeline (the thing
that would *produce* skills) is itself not yet built.

**Assessment:** A full Skill Graph service (lifecycle: propose/approve/deprecate/
version; skill search; orchestrator skill-invocation) is infrastructure with **nothing
to operate on** at first release, because no corpus of approved learnings exists yet.
The genuinely valuable V1 piece is the **human-gated Learning commit**, and its
natural output is a **Skill node** ("Become Skill"). That minimal representation gives
the lineage and is forward-compatible with a full service later.

**Decision: V1 keeps a MINIMAL skill capability** (Skill nodes created only via
approved Learning commit, plus `forge skill list|show`). **DEFER the full Skill Graph
service** (lifecycle/versioning/search/invocation) to V2.

---

## Formal Amendment

### V1 scope (final)
1. All implemented subsystems (P0–P6.6): config/ports/observability; storage
   (SQLite+YAML); memory + lifecycle; knowledge graph + `why`; repo intelligence;
   compression; context assembly; token intelligence; provider layer (Claude/Ollama
   +stubs); provider intelligence; agent orchestrator; advisory system + grounding;
   portability **services**; project (L3) + user (L2) knowledge layers.
2. **Learning Engine — human-gated review/approve/reject/commit** (no auto-promotion;
   approval provenance). Commit may **create a Skill node** ("Become Skill").
3. **Minimal Skill capability** — Skill nodes via approved commit; `forge skill
   list|show`. (No lifecycle/versioning/search/invocation.)
4. **CLI completion** — wire existing `export`/`import`/`backup` services to CLI; add
   `forge init`. **`forge install` removed from V1** (installation is `uv tool
   install` / pip; documented, not a feature).
5. **Documentation reconciliation** — fix Execution-agent naming drift (D1); record the
   MCP V1→V2 decision (C1).
6. **Live provider smoke** — key-gated release gate (run outside the sandbox); not a
   code deliverable.

### V2 scope (deferred)
- **MCP stdio adapter + CLI↔MCP parity** (transport seam preserved).
- **Full Skill Graph service** — propose/approve/deprecate/version, skill search,
  orchestrator skill-invocation.
- **Advisory enhancements** — auto-evidence harvesting (tests/criteria), automated
  cross-command session lineage, greenfield (no-focus-node) grounding.
- Already-V2 items: vector/embedding retrieval, dashboard, voice, socket/HTTP MCP,
  scheduled backups, auto-engaged metric routing, organization layer (L4/V3).

### Rationale
Deliver the **token-efficiency core on the guaranteed CLI surface** in the shortest
credible path; honor the Architecture's own "does not require MCP" principle; avoid
building MCP + full Skill infrastructure that cannot meaningfully contribute to (or
even be verified for) the first usable release. All deferrals are **additive** later
because the adapter/services seams and the `Skill` node type already exist.

### Migration impact
- **Additive only; no breaking changes.** No storage schema change, no
  `schema_version` bump (ADR 0008 generic store). Skill nodes reuse the existing
  `NodeType.SKILL` + `uses_skill` edge — **no data migration**.
- **Deferring MCP:** no code exists to remove; the transport-adapter pattern + shared
  services layer remain ready for a V2 MCP transport.
- **Deferring full Skill Graph:** the V1 minimal Skill node is forward-compatible with
  a future full service (same node type/edges).
- **Existing 208 tests unaffected.** ADR 0012 records the decision; Architecture V1
  scope list + roadmap updated; ADR 0007 cross-referenced.

### Acceptance-criteria changes
- **Removed from V1:** MCP parity AC (→ V2); full Skill Graph CRUD/lifecycle ACs
  (→ V2); `forge install` AC (not a feature).
- **Kept/added to V1:**
  - Learning: review/approve/reject/commit transitions are **human-only**; **no
    auto-promotion** (guard); approval records provenance; **commit creates a Skill
    node**; full lineage queryable.
  - Skill (minimal): skills exist **only** via approved commit; `forge skill list|show`.
  - Portability CLI: `export`→`import` round-trips; `backup` writes + prunes; `forge
    init` idempotent.
  - Docs: Architecture + amendment agree on agent names; MCP V1→V2 recorded.
  - Live smoke: one real Claude + one real Ollama generate returns text + usage
    (key-gated; skipped without creds).

### Resulting "V1 complete" definition
V1 = (current P0–P6.6) **+ Learning human-gated commit with minimal Skill promotion +
portability CLI + `forge init` + doc reconciliation + live-provider smoke.** MCP and
the full Skill Graph are explicitly **V2**.

## Confidence
**High.** The deferrals are supported by the Architecture's own principles (ADR 0007)
and by the dependency reality (Skill value requires accrued learnings; MCP adds an
unverifiable dependency). Risk is low and fully reversible (additive seams). The only
open point is stakeholder acceptance of deferring two originally-listed V1 items.
