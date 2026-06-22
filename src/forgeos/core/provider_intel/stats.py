"""Provider stats recorder + scorecards.

Each provider call emits a stats event; stats accumulate per (provider, model) in
the ``provider_stats`` collection. Scorecards derive avg/p95 latency and success
rate for routing and ``forge provider stats``.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable

from forgeos._time import utcnow
from forgeos.catalog import Collections
from forgeos.core.provider_intel.models import ProviderScorecard, ProviderStat
from forgeos.core.provider_intel.pricing import cost
from forgeos.ports.storage import StoragePort

Clock = Callable[[], datetime.datetime]
_SAMPLE_CAP = 200


def _percentile(samples: list[float], pct: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    index = min(len(ordered) - 1, round(pct * (len(ordered) - 1)))
    return round(ordered[index], 3)


class StatsRecorder:
    """Persist and aggregate provider call statistics."""

    def __init__(self, store: StoragePort, clock: Clock = utcnow) -> None:
        self._store = store
        self._clock = clock

    def record(
        self,
        provider: str,
        model: str,
        *,
        tokens_in: int,
        tokens_out: int,
        latency_ms: float,
        success: bool,
        error: str | None = None,
    ) -> ProviderStat:
        """Record one call and return the updated cumulative stat."""
        key = f"{provider}:{model}"
        row = self._store.get(Collections.PROVIDER_STATS, key)
        stat = (
            ProviderStat.model_validate(row)
            if row
            else ProviderStat(provider=provider, model=model)
        )

        stat.calls += 1
        stat.tokens_in += tokens_in
        stat.tokens_out += tokens_out
        stat.est_cost = round(stat.est_cost + cost(provider, model, tokens_in, tokens_out), 6)
        stat.sum_latency_ms += latency_ms
        stat.latency_samples = [*stat.latency_samples, latency_ms][-_SAMPLE_CAP:]
        if success:
            stat.successes += 1
        else:
            stat.errors += 1
            label = error or "error"
            stat.error_breakdown[label] = stat.error_breakdown.get(label, 0) + 1
        stat.last_seen_at = self._clock().isoformat()
        self._store.put(Collections.PROVIDER_STATS, key, stat.model_dump(mode="json"))
        return stat

    def scorecards(self) -> list[ProviderScorecard]:
        """Return computed scorecards, sorted by provider then model."""
        cards: list[ProviderScorecard] = []
        for row in self._store.query(Collections.PROVIDER_STATS):
            stat = ProviderStat.model_validate(row)
            cards.append(
                ProviderScorecard(
                    provider=stat.provider,
                    model=stat.model,
                    calls=stat.calls,
                    tokens_in=stat.tokens_in,
                    tokens_out=stat.tokens_out,
                    est_cost=stat.est_cost,
                    avg_latency_ms=(
                        round(stat.sum_latency_ms / stat.calls, 3) if stat.calls else 0.0
                    ),
                    p95_latency_ms=_percentile(stat.latency_samples, 0.95),
                    success_rate=round(stat.successes / stat.calls, 4) if stat.calls else 0.0,
                    error_breakdown=stat.error_breakdown,
                )
            )
        return sorted(cards, key=lambda c: (c.provider, c.model))
