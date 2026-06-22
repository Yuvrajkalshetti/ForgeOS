"""Provider port — the single interface all AI providers implement.

Claude and Ollama are wired in V1 (P6); OpenAI/Gemini are interface stubs.
Provider-specific code lives entirely in adapters; swapping a provider touches
only its adapter and config.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class Message:
    """A single chat message."""

    role: str
    content: str


@dataclass(frozen=True)
class ProviderRequest:
    """A normalized generation request, provider-agnostic."""

    messages: list[Message]
    model: str
    max_tokens: int = 1024
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Usage:
    """Token usage as reported by the provider (authoritative actual)."""

    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class ProviderResult:
    """A normalized generation result with usage and latency for ProviderIntel."""

    text: str
    model: str
    usage: Usage
    latency_ms: float
    raw: dict[str, Any] = field(default_factory=dict)


class ProviderPort(Protocol):
    """Async text generation. Implementations expose a stable ``name``."""

    name: str

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        """Generate a completion for ``request``."""
        ...
