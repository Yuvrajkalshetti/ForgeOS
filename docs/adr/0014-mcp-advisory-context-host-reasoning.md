# ADR 0014 — MCP advisory grounding via host-model reasoning

- Status: Accepted
- Date: 2026-06-22
- Extends: ADR 0007 (mcp-stdio-only-v1); supersedes the `forgeos_mentor` decision in ADR 0013

## Context

ADR 0013 exposed `forgeos_mentor` as an MCP tool that calls the configured LLM
provider to produce a recommendation. That design is inherited from the V1 CLI era,
where there was no host model. Inside an MCP host (Claude Code / Claude Desktop), the
host **is** the reasoning model, so a tool that makes its own provider call is:

- redundant (a second model doing what the host is already there to do), and
- a hard dependency on an external provider (Anthropic API key or a local Ollama),
  which defeats the goal of running ForgeOS purely through Claude Code.

Mentor's pipeline has two parts, and only one needs a model:
1. **Grounding** — assembling a deterministic, token-budgeted `ContextBundle` from
   existing knowledge (cards, memory, ADRs, repo profile, decisions, findings). This
   is **provider-free** (`AdvisoryContextBuilder.for_mentor`).
2. **Reasoning** — turning that grounding into a recommendation (the only LLM step).

## Decision

Replace the provider-calling `forgeos_mentor` MCP tool with a read-only
`forgeos_advisory_context` tool that returns the grounding bundle. The **host model**
(Claude Code) performs the reasoning over that grounding.

The tool builds the bundle with **no token ledger** (`AdvisoryContextBuilder(..., )`
leaves `ledger=None`), so `ContextAssembler.assemble` skips its `TOKEN_EVENTS` write —
the tool is genuinely read-only.

Consequently **all seven** MCP tools are now read-only (`readOnlyHint=true`) and the
MCP server requires **no provider, API key, or Ollama** at all.

`forge mentor` (the CLI, provider-backed) is unchanged — this only changes what the
MCP surface exposes.

## Consequences

- ForgeOS works fully inside Claude Code with zero external model dependency.
- The read-only invariant test additionally asserts `TOKEN_EVENTS` is untouched,
  guarding against a regression that re-introduces the ledger write.
- If a fully-automated recommendation (not host-driven) is ever wanted, it belongs in
  the CLI or a separate, clearly provider-dependent surface — not the read-only MCP set.
