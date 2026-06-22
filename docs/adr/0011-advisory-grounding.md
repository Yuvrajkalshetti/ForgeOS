# ADR 0011: Advisory grounding via Context Assembly; deterministic priority tiers

- **Status:** accepted
- **Date:** 2026-06-21
- **Phase:** P6.6

## Context
Mentor/Auditor (P6.5) were `prompt → LLM → response`: they did not consume the
knowledge ForgeOS already holds. ForgeOS's value is *fewer tokens, better context*,
so advisors should be grounded in existing knowledge before Learning (P7).

## Decision
Add `core/advisory/context.py` → `AdvisoryContextBuilder`, which composes a single
budgeted `ContextBundle` from existing components only — cards, memory, ADRs (files),
repo profile, decisions, past audit findings (Mentor); acceptance criteria, decisions,
past findings, cards, evidence (Auditor). It **reuses** Context Assembly
(`ContextAssembler.assemble`) and Token Intelligence (`TokenLedger`). It adds **no**
storage, graph, or provider abstraction, and uses **no** vectors/embeddings/semantic
retrieval. The builder is **provider-free**; only Mentor/Auditor call the LLM.

Two refinements (stakeholder-directed):
1. **Deterministic priority tiers** replace float weights. `context_assembly.models.TIER`
   orders kinds: card < criteria < decision < finding < adr < evidence < repo_profile
   < memory < source < stub. Assembly sorts by `(tier, gather_order, ref)`.
2. **Gather strategy:** graph-reachable items first, then recent-N fill (decisions and
   findings), preserved by gather order within a tier.

**AC11 — cards before source escalation.** For a subject, content escalates
**Card → Memory → Source**: a valid card wins; raw source is used only when the card
is missing/stale or `--source` is explicitly set. (Card validity for a File = stored
`source_hash` matches the node's current hash.)

Mentor/Auditor accept an optional `grounding: ContextBundle`; its rendered text is fed
to the provider, and the included item refs are persisted on the
`MentorRecommendation`/`AuditFinding` node (`grounding_refs`) for lineage.

## Consequences
- Advisors are grounded, token-budgeted, and auditable (manifest + recorded savings).
- ContextItem/ManifestEntry now carry `tier` (int) instead of a float `score`; P5
  behavior preserved (cards still rank first) — a small, regression-guarded refactor.
- No new storage/graph/provider; backward compatible (ADR 0008; no schema bump).
- Determinism preserved end-to-end; advisory boundary guarantees (ADR 0010) intact.
