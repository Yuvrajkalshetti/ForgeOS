from __future__ import annotations

from forgeos.core.provider_intel import Router, StatsRecorder, cost
from forgeos.core.provider_intel.models import ProviderScorecard
from forgeos.testing.fakes import InMemoryStorage


def test_cost_table_and_local_free() -> None:
    assert cost("claude", "claude-opus-4-8", 1_000_000, 0) == 15.0
    assert cost("ollama", "llama3.1", 1_000_000, 1_000_000) == 0.0
    assert cost("unknown", "x", 1_000_000, 0) == 0.0


def test_recorder_accumulates_metrics() -> None:
    rec = StatsRecorder(InMemoryStorage())
    rec.record("claude", "m", tokens_in=100, tokens_out=50, latency_ms=10.0, success=True)
    rec.record("claude", "m", tokens_in=100, tokens_out=50, latency_ms=30.0, success=True)
    rec.record("claude", "m", tokens_in=0, tokens_out=0, latency_ms=5.0, success=False, error="Timeout")
    card = rec.scorecards()[0]
    assert card.calls == 3
    assert card.tokens_in == 200
    assert card.tokens_out == 100
    assert card.success_rate == round(2 / 3, 4)
    assert card.avg_latency_ms == 15.0
    assert card.p95_latency_ms == 30.0
    assert card.error_breakdown == {"Timeout": 1}
    assert card.est_cost > 0


def test_router_pinned_explains_selection_and_rejections() -> None:
    decision = Router("pinned").select("claude", ["claude", "ollama"])
    assert decision.selected == "claude"
    assert "pinned" in decision.reason
    assert decision.rejected == [{"name": "ollama", "reason": "not the configured default"}]


def test_router_cheapest_uses_scorecards() -> None:
    cards = [
        ProviderScorecard(provider="claude", model="m", calls=1, tokens_in=0, tokens_out=0,
                          est_cost=0.50, avg_latency_ms=10, p95_latency_ms=10, success_rate=1.0),
        ProviderScorecard(provider="ollama", model="m", calls=1, tokens_in=0, tokens_out=0,
                          est_cost=0.0, avg_latency_ms=50, p95_latency_ms=50, success_rate=1.0),
    ]
    decision = Router("cheapest").select("claude", ["claude", "ollama"], cards)
    assert decision.selected == "ollama"
    assert "cheapest" in decision.reason
    assert decision.rejected[0]["name"] == "claude"


def test_router_falls_back_to_default_without_stats() -> None:
    decision = Router("fastest").select("claude", ["claude", "ollama"], [])
    assert decision.selected == "claude"  # no stats -> pinned fallback
