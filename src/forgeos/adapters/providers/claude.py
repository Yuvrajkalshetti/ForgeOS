"""Anthropic Claude provider adapter.

Request building and response parsing are pure (and unit-tested); the HTTP client
is injectable so it can be exercised with ``httpx.MockTransport`` (no network).
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from forgeos.ports.provider import ProviderRequest, ProviderResult, Usage

_API_VERSION = "2023-06-01"


class ClaudeProvider:
    """Calls the Anthropic Messages API."""

    name = "claude"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.anthropic.com",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = client

    @staticmethod
    def build_payload(request: ProviderRequest) -> dict[str, Any]:
        """Translate a ProviderRequest into an Anthropic Messages payload."""
        system = "\n".join(m.content for m in request.messages if m.role == "system")
        messages = [
            {"role": m.role, "content": m.content}
            for m in request.messages
            if m.role != "system"
        ]
        payload: dict[str, Any] = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": messages,
        }
        if system:
            payload["system"] = system
        return payload

    @staticmethod
    def parse_response(data: dict[str, Any], model: str, latency_ms: float) -> ProviderResult:
        """Parse an Anthropic Messages response into a ProviderResult."""
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        usage_raw = data.get("usage", {})
        usage = Usage(
            input_tokens=int(usage_raw.get("input_tokens", 0)),
            output_tokens=int(usage_raw.get("output_tokens", 0)),
        )
        return ProviderResult(text=text, model=data.get("model", model), usage=usage,
                              latency_ms=latency_ms, raw=data)

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        client = self._client or httpx.AsyncClient(timeout=60.0)
        started = time.perf_counter()
        try:
            response = await client.post(
                f"{self._base_url}/v1/messages",
                json=self.build_payload(request),
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": _API_VERSION,
                    "content-type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()
        finally:
            if self._client is None:
                await client.aclose()
        latency_ms = (time.perf_counter() - started) * 1000
        return self.parse_response(data, request.model, latency_ms)
