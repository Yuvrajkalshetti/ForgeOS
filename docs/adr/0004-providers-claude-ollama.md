# ADR 0004: Wire Claude + Ollama; stub OpenAI/Gemini

- **Status:** accepted
- **Date:** 2026-06-20

## Context
The provider abstraction must be proven against both a cloud and a local backend
from day one to avoid lock-in.

## Decision
Implement Claude (cloud reference) and Ollama (local reference) adapters in V1.
OpenAI and Gemini are interface stubs raising a clear `NotImplementedError`.

## Consequences
- Real cloud+local coverage validates the `ProviderPort`.
- More upfront adapter work; mitigated by recorded-fixture contract tests.
