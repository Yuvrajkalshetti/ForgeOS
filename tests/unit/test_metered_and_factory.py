from __future__ import annotations

import asyncio

import pytest

from forgeos.adapters.providers import MeteredProvider
from forgeos.adapters.providers.factory import ProviderUnavailable, build_provider
from forgeos.adapters.tokenizer import LocalEstimator
from forgeos.config.models import ForgeConfig
from forgeos.core.provider_intel import StatsRecorder
from forgeos.core.token_intel import TokenLedger
from forgeos.ports.provider import Message, ProviderRequest
from forgeos.testing.fakes import FailIfCalledProvider, FakeProvider, InMemoryStorage


def _req() -> ProviderRequest:
    return ProviderRequest(messages=[Message("user", "hi")], model="m")


def test_metered_records_stats_and_actual_tokens() -> None:
    store = InMemoryStorage()
    recorder = StatsRecorder(store)
    ledger = TokenLedger(store)
    provider = MeteredProvider(FakeProvider(reply="hello"), recorder, ledger, LocalEstimator())

    asyncio.run(provider.generate(_req()))

    card = recorder.scorecards()[0]
    assert card.calls == 1 and card.success_rate == 1.0
    report = ledger.report()
    assert report.events == 1
    assert report.total_actual == len("hello")  # FakeProvider sets output_tokens=len(reply)


def test_metered_records_failure_and_reraises() -> None:
    store = InMemoryStorage()
    recorder = StatsRecorder(store)
    provider = MeteredProvider(FailIfCalledProvider(), recorder)
    with pytest.raises(AssertionError):
        asyncio.run(provider.generate(_req()))
    card = recorder.scorecards()[0]
    assert card.success_rate == 0.0
    assert card.error_breakdown == {"AssertionError": 1}


def test_factory_claude_requires_key() -> None:
    config = ForgeConfig()  # default provider = claude
    with pytest.raises(ProviderUnavailable, match="API key"):
        build_provider(config, environ={})


def test_factory_builds_claude_with_key_and_ollama() -> None:
    config = ForgeConfig()
    claude = build_provider(config, environ={"ANTHROPIC_API_KEY": "k"})
    assert claude.name == "claude"

    config.providers.default = "ollama"
    assert build_provider(config, environ={}).name == "ollama"


def test_factory_returns_stub_for_openai() -> None:
    config = ForgeConfig()
    config.providers.default = "openai"
    assert build_provider(config, environ={}).name == "openai"
