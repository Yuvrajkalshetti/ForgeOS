from __future__ import annotations

from forgeos.catalog import Collections
from forgeos.core.token_intel import TokenLedger
from forgeos.testing.fakes import InMemoryStorage


def test_record_computes_savings_from_estimate() -> None:
    ledger = TokenLedger(InMemoryStorage())
    event = ledger.record(
        "req1", "node:1", "context-assembly", "n/a",
        tokens_estimated=30, tokens_raw_equiv=100,
    )
    assert event.tokens_saved == 70


def test_record_prefers_actual_when_present() -> None:
    ledger = TokenLedger(InMemoryStorage())
    event = ledger.record(
        "req1", "s", "claude", "m",
        tokens_estimated=30, tokens_raw_equiv=100, tokens_actual=40,
    )
    assert event.tokens_saved == 60  # 100 - actual(40), not estimate


def test_report_aggregates_and_computes_ratio() -> None:
    store = InMemoryStorage()
    ledger = TokenLedger(store)
    ledger.record("r1", "s", "context-assembly", "n/a", tokens_estimated=20, tokens_raw_equiv=100)
    ledger.record("r2", "s", "context-assembly", "n/a", tokens_estimated=10, tokens_raw_equiv=100)
    report = ledger.report()
    assert report.events == 2
    assert report.raw_tokens == 200
    assert report.total_saved == 170
    assert report.compressed_tokens == 30
    assert report.compression_ratio == 0.15
    assert report.saved_by_provider == {"context-assembly": 170}


def test_report_empty_is_neutral_ratio() -> None:
    assert TokenLedger(InMemoryStorage()).report().compression_ratio == 1.0


def test_events_persisted() -> None:
    store = InMemoryStorage()
    TokenLedger(store).record("r", "s", "p", "m", tokens_estimated=1, tokens_raw_equiv=2)
    assert len(store.query(Collections.TOKEN_EVENTS)) == 1
