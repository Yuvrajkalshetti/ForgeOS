"""Token savings ledger.

Records every accounted interaction and aggregates savings. ``tokens_saved`` is the
difference between the raw-equivalent cost (what naive context would have cost) and
what was actually sent — using the provider-reported actual when available, else the
pre-flight estimate (dual-source accounting, plan §11.2).
"""

from __future__ import annotations

import datetime
from collections.abc import Callable

from forgeos.catalog import Collections
from forgeos.core.token_intel.models import TokenEvent, TokenReport
from forgeos.ports.storage import StoragePort

Clock = Callable[[], datetime.datetime]


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class TokenLedger:
    """Persist and aggregate :class:`TokenEvent` records."""

    def __init__(self, store: StoragePort, clock: Clock = _utcnow) -> None:
        self._store = store
        self._clock = clock

    def record(
        self,
        request_id: str,
        scope_ref: str,
        provider: str,
        model: str,
        *,
        tokens_estimated: int = 0,
        tokens_raw_equiv: int = 0,
        tokens_actual: int | None = None,
    ) -> TokenEvent:
        """Record one interaction and return the stored event."""
        billed = tokens_actual if tokens_actual is not None else tokens_estimated
        event = TokenEvent(
            request_id=request_id,
            scope_ref=scope_ref,
            provider=provider,
            model=model,
            tokens_estimated=tokens_estimated,
            tokens_actual=tokens_actual,
            tokens_raw_equiv=tokens_raw_equiv,
            tokens_saved=max(0, tokens_raw_equiv - billed),
            created_at=self._clock(),
        )
        self._store.put(Collections.TOKEN_EVENTS, event.id, event.model_dump(mode="json"))
        return event

    def report(self) -> TokenReport:
        """Aggregate all recorded events into a :class:`TokenReport`."""
        events = [
            TokenEvent.model_validate(row)
            for row in self._store.query(Collections.TOKEN_EVENTS)
        ]
        report = TokenReport(events=len(events))
        for event in events:
            report.total_estimated += event.tokens_estimated
            report.total_actual += event.tokens_actual or 0
            report.total_raw_equiv += event.tokens_raw_equiv
            report.total_saved += event.tokens_saved
            report.saved_by_provider[event.provider] = (
                report.saved_by_provider.get(event.provider, 0) + event.tokens_saved
            )
        return report
