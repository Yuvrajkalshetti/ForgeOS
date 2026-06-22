# ADR 0009: Compression is deterministic and provider-free (no LLM)

- **Status:** accepted (supersedes the provider-backed compression note in Architecture Rev 2 §9)
- **Date:** 2026-06-20

## Context
Architecture Rev 2 described the Compression Engine as consuming a provider/LLM to
write knowledge-card prose. Stakeholder direction for P5 requires that **card
generation has no LLM dependency** and that **compression remains provider-free**,
matching the determinism guarantees already in place for RepoIntel and Context
Assembly. Determinism also makes cards reproducible and cheap, and removes a
runtime/token cost.

## Decision
Knowledge cards are generated **deterministically from the knowledge graph and the
RepoProfile** — no provider, no network, no LLM. Card fields are derived from facts
already extracted by RepoIntel (P4):

- ``purpose`` — templated from node type, language, size, and structure.
- ``modules`` — contained files (for Module targets), from ``contains`` edges.
- ``dependencies`` — from ``depends_on`` edges (internal Module vs external Dependency).
- ``key_decisions`` — from ``decided_by`` / ``affects`` edges to Decision nodes.
- ``risks`` / ``recent_changes`` — from churn hotspots in the RepoProfile.

The ``provider`` field records ``{name: "forgeos", model: "deterministic"}``. The
card JSON Schema and ``extensions`` mechanism are unchanged.

## Consequences
- Compression is reproducible (same inputs → identical card) and free.
- ``forge compress`` works without the provider layer (no P6 dependency).
- ``forgeos.core.compression`` must not import ``forgeos.ports.provider`` — enforced
  by a static guard test, like RepoIntel (ADR 0005).
- Cards are factual/structural rather than prose-rich; richer narrative summaries
  (if ever wanted) would be a separate, optional, clearly-bounded future feature.
