# ADR 0001: Hexagonal (ports-and-adapters) architecture

- **Status:** accepted
- **Date:** 2026-06-20

## Context
ForgeOS must support multiple providers, transports, and storage backends, stay
local-first, and remain testable without live services.

## Decision
Adopt a layered hexagonal architecture: a pure `core/` domain depends only on
abstract `ports/`; concrete `adapters/` implement them. `core/` never imports
`adapters/`; dependencies point inward only.

## Alternatives considered
- Framework-centric (FastAPI/Django) — heavy, couples domain to transport.
- Direct provider calls in core — defeats provider neutrality and testability.

## Consequences
- Swapping a provider/transport/storage touches only its adapter + config.
- Unit tests run against in-memory fakes.
- Slight indirection overhead, justified by V1's multi-adapter scope.
