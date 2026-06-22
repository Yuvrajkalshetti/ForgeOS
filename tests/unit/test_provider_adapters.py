from __future__ import annotations

import asyncio

import httpx
import pytest

from forgeos.adapters.providers import (
    ClaudeProvider,
    GeminiProvider,
    OllamaProvider,
    OpenAIProvider,
)
from forgeos.ports.provider import Message, ProviderRequest


def _request() -> ProviderRequest:
    return ProviderRequest(
        messages=[Message("system", "be brief"), Message("user", "hi")],
        model="claude-opus-4-8",
        max_tokens=64,
    )


def test_claude_payload_splits_system_and_messages() -> None:
    payload = ClaudeProvider.build_payload(_request())
    assert payload["system"] == "be brief"
    assert payload["messages"] == [{"role": "user", "content": "hi"}]
    assert payload["max_tokens"] == 64


def test_claude_generate_with_mock_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "k"
        assert request.headers["anthropic-version"]
        return httpx.Response(
            200,
            json={
                "model": "claude-opus-4-8",
                "content": [{"type": "text", "text": "hello"}],
                "usage": {"input_tokens": 5, "output_tokens": 2},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = ClaudeProvider("k", client=client)
    result = asyncio.run(provider.generate(_request()))
    assert result.text == "hello"
    assert result.usage.input_tokens == 5
    assert result.usage.output_tokens == 2
    assert result.latency_ms >= 0
    asyncio.run(client.aclose())


def test_ollama_generate_with_mock_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        return httpx.Response(
            200,
            json={
                "model": "llama3.1",
                "message": {"role": "assistant", "content": "yo"},
                "prompt_eval_count": 7,
                "eval_count": 3,
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OllamaProvider(client=client)
    result = asyncio.run(provider.generate(ProviderRequest(messages=[Message("user", "hi")], model="llama3.1")))
    assert result.text == "yo"
    assert result.usage.input_tokens == 7
    assert result.usage.output_tokens == 3
    asyncio.run(client.aclose())


@pytest.mark.parametrize("provider", [OpenAIProvider(), GeminiProvider()])
def test_stub_providers_raise(provider: object) -> None:
    with pytest.raises(NotImplementedError):
        asyncio.run(provider.generate(_request()))  # type: ignore[attr-defined]
