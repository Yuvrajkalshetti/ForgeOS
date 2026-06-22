# Focused Audit — MCP value & Skill "Become Skill" (evidence-based)

Method: repository inspection. Auditor stance: claims need evidence.

## MCP
**Q: What user capability is lost if MCP is absent?**
A real, unique one: **external MCP hosts (Claude Desktop / Claude Code / other MCP
clients) cannot call ForgeOS as structured tools/resources mid-conversation.** With
MCP, the *model itself* (not a human) pulls memory/graph/context-assembly during its
own loop — model-initiated, in-session knowledge retrieval with discoverable tool
schemas. That is the natural delivery of ForgeOS's thesis ("sits between users,
projects, and AI providers") when the consumer is a third-party AI host.
Without MCP, an external host can only shell out to `forge …` and parse text — possible
but degraded (no tool schema, no resources, no structured discovery).
**Verdict: the claim "MCP adds no unique capability" is FALSE.** MCP's unique value is
*external-AI-host integration*, which the CLI cannot natively provide to a host.

**Q: Is the CLI truly feature-complete?**
For **humans / scripts / ForgeOS-internal flows: yes** — 11 command groups cover every
subsystem (`scan, compress, context, memory, graph, tokens, provider, agent, mentor,
audit, config`), and ForgeOS's own agent/advisory paths call providers directly, so
they need no MCP. Caveat: `export/import/backup` and `init` are **not yet wired**
(already V1-build tasks), so CLI is "capability-complete" but not "command-complete"
until those land.
For **external AI-host consumption: no** — there is no substitute for MCP's tool/resource
surface.

**Cost note (evidence):** there is **no shared services facade** — `services/` holds
only `portability.py`, and CLI commands wire engines inline (e.g. `memory.py:_open`
builds `SnapshotStore` + `MemoryService` itself). So an MCP transport cannot "just
wrap" a facade; it would require extracting one first (good architecture, but real
work) plus an MCP SDK dependency (unverifiable in this environment).

## Skill Graph
**Q: Can Learning be considered complete without Skill promotion?**
**No.** The architecture's Learning workflow ends in "Become Skill." Today Learning is
emit/list only (`core/learning/proposal.py`); `ProposalStatus.APPROVED` exists as an
enum value but **nothing transitions to it** and **no skill is created**. Learning
without a promotion step is incomplete by the architecture's own definition.

**Q: Where exactly does "Become Skill" happen?**
**Nowhere today.** Evidence: no `approve`/`commit` function, no skill creation, no
`core/skill/`. It is *planned* to happen in the Learning **commit** step (commit →
create a `Skill` node). So "minimal Skill promotion" does **not yet exist** — it is V1
build work, not a present fact.

## Reconciliation against your conditional
You said: *if (MCP adds no unique capability) and (Minimal Skill Promotion exists),
then freeze.* Evidence shows **both premises are currently false**:
1. MCP **does** add unique capability (external-host integration).
2. Minimal Skill Promotion **does not exist yet** (it's planned in Learning commit).

Therefore the freeze is **not** justified on those exact tests as written.

## What is actually defensible
- **Skill:** defer the **full Skill Graph lifecycle** to V2 (agreed). Keep **minimal
  promotion in the V1 build** — and recognize it must be *built*; Learning isn't
  complete until "Become Skill" exists in the commit step.
- **MCP:** deferring MCP to V2 is defensible **only as a deliberate "CLI-first V1"
  product choice**, with eyes open that it postpones *external-AI-host integration* —
  **not** because MCP is valueless (it isn't). If "usable inside Claude Desktop/Code
  out of the box" is a V1 goal, MCP belongs in V1, and a **services-facade extraction**
  should be planned first (it also cleans up CLI↔MCP parity).

## Recommendation
- Confirm Skill decision as-is (full lifecycle → V2; minimal promotion → V1 build).
- For MCP, choose explicitly on **target audience**, not on a value claim:
  - **V1 = CLI-first** (humans/scripts/ForgeOS-internal): defer MCP to V2 — acceptable,
    fastest, loses only external-host integration *for now*.
  - **V1 = "works as tools inside an MCP host"**: keep MCP in V1; first extract a
    services facade, then add the stdio transport + parity.
- Either way, freeze the scope on a **true** rationale.

## Confidence
**High** on the findings (all repository-verified). The remaining decision is a
product call (who is V1 for?), which is the stakeholder's to make — exactly the
assumption you flagged.
