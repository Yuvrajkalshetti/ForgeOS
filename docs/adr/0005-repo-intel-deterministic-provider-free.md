# ADR 0005: Repository Intelligence is deterministic and provider-free

- **Status:** accepted
- **Date:** 2026-06-20

## Context
Repository ingest must be cheap, repeatable, and free of token cost or
non-determinism.

## Decision
RepoIntel performs **no provider/LLM calls** during scanning, graph construction,
dependency discovery, hotspot analysis, or incremental indexing. Enforced by:
(1) `forgeos.core.repo_intel` not importing the provider port — verified by a
static import guard test; and (2) ingest paths exercised with a
`FailIfCalledProvider` that raises if invoked.

## Consequences
- Ingest is fast, deterministic, and reproducible against the golden corpus.
- Semantic enrichment is the Compression Engine's job, not RepoIntel's.
