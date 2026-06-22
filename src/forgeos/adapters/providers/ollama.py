"""Ollama provider adapter (local).

Same shape as the Claude adapter: pure payload/parse helpers plus an injectable
HTTP client. Lower default concurrency is enforced by the orchestrator/config, not
here.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from forgeos.ports.provider import ProviderRequest, ProviderResult, Usage


class OllamaProvider:
    """Calls a local Ollama ``/api/chat`` endpoint."""

    name = "ollama"

    def __init__(
        self,
        host: str = "http://localhost:11434",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._host = host.rstrip("/")
        self._client = client

    @staticmethod
    def build_payload(request: ProviderRequest) -> dict[str, Any]:
        """Translate a ProviderRequest into an Ollama chat payload."""
        return {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
        }

    @staticmethod
    def parse_response(data: dict[str, Any], model: str, latency_ms: float) -> ProviderResult:
        """Parse an Ollama chat response into a ProviderResult."""
        text = data.get("message", {}).get("content", "")
        usage = Usage(
            input_tokens=int(data.get("prompt_eval_count", 0)),
            output_tokens=int(data.get("eval_count", 0)),
        )
        return ProviderResult(text=text, model=data.get("model", model), usage=usage,
                              latency_ms=latency_ms, raw=data)

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        client = self._client or httpx.AsyncClient(timeout=120.0)
        started = time.perf_counter()
        try:
            response = await client.post(
                f"{self._host}/api/chat", json=self.build_payload(request)
            )
            response.raise_for_status()
            data = response.json()
        finally:
            if self._client is None:
                await client.aclose()
        latency_ms = (time.perf_counter() - started) * 1000
        return self.parse_response(data, request.model, latency_ms)
