# ADR 0010: Advisory System (Mentor + Auditor), separate from Execution

- **Status:** accepted (architecture amendment)
- **Date:** 2026-06-20
- **Sequencing:** implement after P6, before P7 (phase **P6.5**)

## Context
ForgeOS to date has a single multi-agent capability: the **Execution System**
(Architect/Engineer/QA/Reviewer/Security via the Orchestrator, P6) that *builds
things*. The approved amendment adds an **Advisory System** that *improves decision
and implementation quality* but never executes. It has two agents:

- **Mentor** — works *before* execution; converts vague goals into executable
  strategies, challenges assumptions, prevents over/under-engineering.
- **Auditor** — works *after* planning/implementation; validates evidence,
  compliance, tests, and claims; skeptical by default.

Final approval authority always remains human.

## Decision
Create a new subsystem `forgeos.core.advisory` (Mentor + Auditor), **separate from
`forgeos.core.orchestrator`** (Execution). Advisory agents:

- are provider-backed (they reason), using the existing `ProviderPort`;
- **never** execute, write production code, deploy, merge, or approve;
- emit structured artifacts persisted as **graph nodes** — `MentorRecommendation`
  and `AuditFinding` — with provenance, enabling the traceable chain
  `MentorRecommendation → (human) Decision → Implementation → AuditFinding`.

Separation is enforced two ways: Execution must not import Advisory and Advisory
must not import Execution (static guard test); and Advisory has no code path that
transitions a learning proposal to approved/applied.

## Consequences
- Decision/implementation quality becomes observable and learnable (the chain
  feeds the Learning Engine, human-approved as always).
- Additive graph node/edge types — backward compatible (ADR 0008 generic store; no
  schema_version bump).
- Two new CLI commands (`forge mentor`, `forge audit`) that fail gracefully without
  a configured provider (provider isolation, ADR/P6 behavior preserved).
- Provider-free engines (RepoIntel/Compression/Context Assembly) are unaffected.

## Alternatives considered
- Put Mentor/Auditor inside the Orchestrator — rejected: violates the required
  separation of advisory from execution.
- Make advisory provider-free/templated — rejected: advisory must *reason*; it is
  legitimately provider-backed (unlike RepoIntel/Compression).
