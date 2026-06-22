"""Interface stubs for not-yet-implemented providers (plan: OpenAI, Gemini).

They implement :class:`ProviderPort` so the abstraction holds, and raise a clear
error if actually invoked.
"""

from __future__ import annotations

from forgeos.ports.provider import ProviderRequest, ProviderResult


class _StubProvider:
    name = "stub"

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        raise NotImplementedError(
            f"the {self.name!r} provider is not implemented in V1; "
            f"use 'claude' or 'ollama'"
        )


class OpenAIProvider(_StubProvider):
    name = "openai"


class GeminiProvider(_StubProvider):
    name = "gemini"
