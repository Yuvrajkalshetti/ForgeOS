"""In-memory fakes implementing each port.

Unit tests run against these — no live providers, no disk. ``FailIfCalledProvider``
exists specifically to enforce the directive that the Repository Intelligence
Engine (P4) performs zero provider calls during ingest: wire it in and any call
raises.
"""

from __future__ import annotations

import copy
import time

from forgeos.ports.provider import Message, ProviderRequest, ProviderResult, Usage
from forgeos.ports.storage import Record
from forgeos.ports.vector import VectorMatch


class InMemoryStorage:
    """Dict-backed :class:`~forgeos.ports.storage.StoragePort` implementation."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, Record]] = {}

    def put(self, collection: str, record_id: str, data: Record) -> None:
        self._data.setdefault(collection, {})[record_id] = copy.deepcopy(data)

    def get(self, collection: str, record_id: str) -> Record | None:
        found = self._data.get(collection, {}).get(record_id)
        return copy.deepcopy(found) if found is not None else None

    def delete(self, collection: str, record_id: str) -> None:
        self._data.get(collection, {}).pop(record_id, None)

    def query(self, collection: str, where: Record | None = None) -> list[Record]:
        rows = self._data.get(collection, {}).values()
        if not where:
            return [copy.deepcopy(r) for r in rows]
        return [
            copy.deepcopy(r)
            for r in rows
            if all(r.get(k) == v for k, v in where.items())
        ]

    def collections(self) -> list[str]:
        return sorted(self._data)


class FakeTokenizer:
    """Deterministic length-based token estimator for tests."""

    def count_text(self, text: str, model: str | None = None) -> int:
        return (len(text) + 3) // 4

    def count_messages(self, messages: list[Message], model: str | None = None) -> int:
        return sum(self.count_text(m.content, model) for m in messages)


class FakeProvider:
    """Returns a canned reply and records every request it receives."""

    name = "fake"

    def __init__(self, reply: str = "ok") -> None:
        self.reply = reply
        self.calls: list[ProviderRequest] = []

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        self.calls.append(request)
        return ProviderResult(
            text=self.reply,
            model=request.model,
            usage=Usage(input_tokens=0, output_tokens=len(self.reply)),
            latency_ms=0.0,
            raw={"fake": True},
        )


class FailIfCalledProvider:
    """A provider that fails if invoked — guards provider-free code paths."""

    name = "fail-if-called"

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        raise AssertionError(
            "provider was called on a path that must remain provider-free"
        )


class NullVectorStore:
    """Disabled vector store for V1 (graph-first retrieval)."""

    enabled = False

    def upsert(self, key: str, vector: list[float], payload: dict[str, object]) -> None:
        raise NotImplementedError("vector store is disabled in V1")

    def search(self, vector: list[float], k: int = 5) -> list[VectorMatch]:
        raise NotImplementedError("vector store is disabled in V1")


def monotonic_ms() -> int:
    """Helper: current monotonic time in milliseconds (for deterministic tests)."""
    return time.monotonic_ns() // 1_000_000
