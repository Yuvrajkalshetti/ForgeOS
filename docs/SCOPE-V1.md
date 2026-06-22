# ForgeOS — V1 Scope Lock

> **Status: LOCKED** (human-approved, 2026-06-21).
> Authoritative definition of what is in / out of ForgeOS V1. This governs all
> planning and Mentor/Auditor evaluation. Do NOT re-open V1 scope unless a critical
> architectural flaw, contradiction, or blocking dependency is discovered — and even
> then, only a human may change scope.

Evidence basis: `docs/AUDIT-mcp-skill.md` (repository-verified). The lock adopts the
audit's **"V1 = CLI-first"** path: defer MCP to V2 as a deliberate product choice (not
because MCP lacks value), keep **minimal** Skill promotion as real V1 build work.

## Locked rules
- The V1 scope is LOCKED. Do not re-open it absent a critical flaw, contradiction, or
  blocking dependency.
- Do not move features into/out of V1 based on implementation effort, schedule
  pressure, or preference.
- Any scope change requires **explicit human approval**.

---

## V1 Definition

### V1 Build Complete (must exist and pass standard gates)
- **P0–P6.6 completed** — ✅ all done, including P6.6 Advisory Intelligence Wiring
  (verified 2026-06-21: 34 advisory tests green, full suite 208). See `HANDOFF.md`.
- Learning **review** workflow
- Learning **approve** workflow
- Learning **reject** workflow
- Learning **commit** workflow
- Human-gated learning only — **no autonomous promotion**
- **Provenance tracking** for all learning decisions
- **Minimal Skill promotion**: Approved Learning → Commit → **Skill Node**
- Skill **listing** and **inspection** (`skill list`, `skill show`)
- **Portability CLI**: `export`, `import`, `backup`
- `forge init`
- **Documentation reconciliation**:
  - Execution-agent naming consistency
  - MCP-scope documentation consistency

### V1 Release Ready (release gates, NOT implementation deliverables)
- Real Claude smoke test
- Real Ollama smoke test
- Provider token reconciliation validation
- Release checklist completion (`docs/RELEASE-CHECKLIST-v1.md`)

---

## Explicitly Deferred to V2

### MCP — deferred to V2
MCP provides external-AI-host integration value but is **not required** for ForgeOS
core functionality. V1 is **CLI-first**, targeting humans, scripts, and ForgeOS-native
workflows. MCP remains an approved future capability. Do not reintroduce MCP into V1
planning without explicit human approval.

> Evidence (`AUDIT-mcp-skill.md`): MCP's unique value is external-AI-host integration
> (the model itself pulling memory/graph/context mid-loop with discoverable schemas),
> which the CLI cannot natively provide. Deferral is a deliberate CLI-first product
> choice, **not** a claim that MCP is valueless. When MCP is taken up (V2), a
> **services-facade extraction** should be planned first (also fixes CLI↔MCP parity).

### Full Skill Graph — deferred to V2
V1 requires only: Skill creation via approved Learning Commit, `skill list`, `skill show`.
Deferred to V2: skill lifecycle management, versioning, deprecation, search, invocation,
advanced skill governance.

---

## Planning Rule
Prioritize completion of the **Knowledge → Learning → Skill loop** before any transport,
integration, UI, dashboard, voice, MCP, or ecosystem-expansion work. The unfinished
**Learning → Skill loop is the highest-priority remaining architectural objective.**

## Mentor Guidance
If future planning attempts to add MCP, Dashboard, Voice, Full Skill Graph, Organization
Layer, Vector Search, or Advanced Advisory features, the Mentor must challenge the
proposal and require explicit justification for why it belongs in V1. Default assumption:
these are V2+ unless human approval changes scope.

## Auditor Guidance
The Auditor must evaluate future work against this locked V1 definition and flag scope
creep, reintroduced V2 features, and changes that violate the approved V1 definition. The
Auditor must **not** classify deferred V2 features as V1 blockers.

## Human Authority
Final approval authority remains human. Mentor cannot approve. Auditor cannot approve.
Execution agents cannot approve. Only a human may: change V1 scope, reclassify V1/V2
features, approve implementation, approve release.
