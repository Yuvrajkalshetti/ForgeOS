# ADR 0003: Graph-first retrieval; no vector database in V1

- **Status:** accepted
- **Date:** 2026-06-20

## Context
Retrieval must be explainable and deterministic; embeddings add a heavy
dependency and compute/token cost.

## Decision
V1 retrieval is bounded graph traversal + structured filters. A `VectorPort` seam
is defined but unwired (disabled), so V2 can add embeddings without core changes.

## Consequences
- Deterministic, auditable context selection.
- Weaker fuzzy recall, accepted for V1 and deferred to V2.
