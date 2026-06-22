from __future__ import annotations

import pytest

from forgeos.ports.provider import Message, ProviderRequest
from forgeos.testing.fakes import (
    FailIfCalledProvider,
    FakeProvider,
    FakeTokenizer,
    InMemoryStorage,
    NullVectorStore,
)


def test_in_memory_storage_put_get_delete() -> None:
    store = InMemoryStorage()
    store.put("nodes", "n1", {"type": "File", "label": "a.py"})
    assert store.get("nodes", "n1") == {"type": "File", "label": "a.py"}
    store.delete("nodes", "n1")
    assert store.get("nodes", "n1") is None


def test_in_memory_storage_isolates_copies() -> None:
    store = InMemoryStorage()
    payload = {"k": [1, 2]}
    store.put("c", "id", payload)
    payload["k"].append(3)
    assert store.get("c", "id") == {"k": [1, 2]}  # stored copy unaffected


def test_in_memory_storage_query_filters() -> None:
    store = InMemoryStorage()
    store.put("nodes", "n1", {"type": "File"})
    store.put("nodes", "n2", {"type": "Module"})
    assert len(store.query("nodes")) == 2
    assert [r["type"] for r in store.query("nodes", {"type": "Module"})] == ["Module"]
    assert store.collections() == ["nodes"]


def test_fake_tokenizer_counts() -> None:
    tok = FakeTokenizer()
    assert tok.count_text("abcd") == 1
    assert tok.count_messages([Message("user", "abcd"), Message("user", "abcd")]) == 2


def test_fake_provider_records_and_replies() -> None:
    import asyncio

    provider = FakeProvider(reply="hello")
    request = ProviderRequest(messages=[Message("user", "hi")], model="m")
    result = asyncio.run(provider.generate(request))
    assert result.text == "hello"
    assert result.model == "m"
    assert provider.calls == [request]


def test_fail_if_called_provider_raises() -> None:
    import asyncio

    provider = FailIfCalledProvider()
    request = ProviderRequest(messages=[Message("user", "hi")], model="m")
    with pytest.raises(AssertionError):
        asyncio.run(provider.generate(request))


def test_null_vector_store_disabled() -> None:
    store = NullVectorStore()
    assert store.enabled is False
    with pytest.raises(NotImplementedError):
        store.search([0.1, 0.2])
