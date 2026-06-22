"""Metering decorator for any provider.

Wraps a :class:`ProviderPort` and records, on every call, provider stats
(latency, tokens, success/error) and — using the provider-reported usage as the
authoritative *actual* — a token event reconciling estimate vs actual (plan §11.2,
§15.2). Failures are recorded then re-raised so the orchestrator can isolate them.
"""

from __future__ import annotations

import time

from forgeos._ids import new_id
from forgeos.core.provider_intel import StatsRecorder
from forgeos.core.token_intel import TokenLedger
from forgeos.ports.provider import ProviderPort, ProviderRequest, ProviderResult
from forgeos.ports.tokenizer import TokenizerPort


class MeteredProvider:
    """A provider wrapper that records stats and token events."""

    def __init__(
        self,
        inner: ProviderPort,
        recorder: StatsRecorder,
        ledger: TokenLedger | None = None,
        estimator: TokenizerPort | None = None,
    ) -> None:
        self._inner = inner
        self._recorder = recorder
        self._ledger = ledger
        self._estimator = estimator
        self.name = inner.name

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        estimated = (
            self._estimator.count_messages(request.messages) if self._estimator else 0
        )
        started = time.perf_counter()
        try:
            result = await self._inner.generate(request)
        except Exception as exc:
            self._recorder.record(
                self._inner.name, request.model,
                tokens_in=0, tokens_out=0,
                latency_ms=(time.perf_counter() - started) * 1000,
                success=False, error=type(exc).__name__,
            )
            raise
        self._recorder.record(
            self._inner.name, request.model,
            tokens_in=result.usage.input_tokens, tokens_out=result.usage.output_tokens,
            latency_ms=result.latency_ms, success=True,
        )
        if self._ledger is not None:
            actual = result.usage.input_tokens + result.usage.output_tokens
            self._ledger.record(
                request_id=new_id("req"),
                scope_ref=request.model,
                provider=self._inner.name,
                model=request.model,
                tokens_estimated=estimated,
                tokens_raw_equiv=estimated,
                tokens_actual=actual,
            )
        return result
