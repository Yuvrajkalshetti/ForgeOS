# ADR 0016: Ownership Intelligence — declared vs observed

- **Status:** Accepted
- **Date:** 2026-06-23
- **Extends:** ADR 0015. **Supersedes** the E4 definition in ADR 0015 (state `READS`/`WRITES`
  ownership) with a rule-based declared/observed model.

## Context

E4 should answer ownership/responsibility questions (domain, layer, criticality, runtime
impact). Static code cannot derive business judgments — criticality, live-money impact — so
those are governance metadata. Domain ownership, however, has two distinct, both-deterministic
sources: human-declared rules, and observed call-graph consumption.

## Decision

1. Ownership is a **deterministic, provider-free, query-time** rule engine — **no new
   persistence, no ownership collection** (computed from rules + the existing E2/E3 graph).
2. **Declared ownership** comes from rules (`<project>/.forgeos/ownership.yaml` + bundled
   generic defaults): match by `symbol` / `name` / `path` (precedence symbol > name > path),
   assigning `domain` / `layer` / `criticality` / `impact`.
3. **Observed ownership** is computed deterministically from the call graph: the majority
   declared-domain among a symbol's direct (resolved) callers; ties broken by sorted name.
4. Every result exposes `declared_owner`, `observed_owner`, `agreement`, `confidence`,
   `matched_by` (plus `layer`/`criticality`/`impact` and the caller distribution) — enabling
   **architectural-drift detection** (declared ≠ observed).
5. **Criticality, runtime impact, business risk, live-trading and governance labels remain
   rule-only** — never inferred from code. Mutation tracking (`READS`/`WRITES`) is **not** used
   (non-goal); impact is *declared*, not *measured*.
6. The trading/domain taxonomy lives in the **project's** `ownership.yaml`, not ForgeOS core
   (which ships only a generic default ruleset + the engine).

`confidence` is a documented deterministic blend: `0.5*declared_tier_weight +
0.5*observed_caller_fraction (+0.1 when declared and observed agree)`, capped at 1.0; with no
callers it is the declared tier weight alone.

## Consequences

- New read-only MCP tools `forgeos_runtime_owner` and `forgeos_runtime_summary`.
- Labels are config assertions, reported with `confidence` + `matched_by`; **over-trust is the
  main risk**, mitigated by that transparency and an `Unknown`/`Unclassified` fallback.
- Out of scope (E5 / future): data flow, runtime tracing, mutation tracking, learning/memory
  integration, ownership-editing UI.
