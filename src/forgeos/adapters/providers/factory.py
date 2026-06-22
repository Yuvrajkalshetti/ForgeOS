"""Provider factory.

Builds the configured provider. Raises :class:`ProviderUnavailable` (rather than
crashing) when a provider cannot be constructed — e.g. a missing API key — so the
CLI can fail gracefully while the rest of ForgeOS keeps working.
"""

from __future__ import annotations

import os

from forgeos.adapters.providers.claude import ClaudeProvider
from forgeos.adapters.providers.ollama import OllamaProvider
from forgeos.adapters.providers.stubs import GeminiProvider, OpenAIProvider
from forgeos.config.models import ForgeConfig
from forgeos.ports.provider import ProviderPort


class ProviderUnavailable(RuntimeError):
    """Raised when the configured provider cannot be constructed."""


def build_provider(
    config: ForgeConfig, environ: dict[str, str] | None = None
) -> ProviderPort:
    """Construct the provider named by ``config.providers.default``."""
    environ = environ if environ is not None else dict(os.environ)
    name = config.providers.default

    if name == "claude":
        api_key = environ.get(config.providers.claude.api_key_env)
        if not api_key:
            raise ProviderUnavailable(
                f"Claude API key not set (${config.providers.claude.api_key_env}); "
                f"configure it or 'forge provider use ollama'"
            )
        return ClaudeProvider(api_key)
    if name == "ollama":
        return OllamaProvider(config.providers.ollama.host)
    if name == "openai":
        return OpenAIProvider()
    if name == "gemini":
        return GeminiProvider()
    raise ProviderUnavailable(f"unknown provider: {name}")
