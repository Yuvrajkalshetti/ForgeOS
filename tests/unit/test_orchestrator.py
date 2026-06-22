from __future__ import annotations

import asyncio

from forgeos.core.orchestrator import (
    AgentResult,
    AgentSpec,
    Finding,
    Orchestrator,
    merge_findings,
)
from forgeos.ports.provider import ProviderRequest, ProviderResult, Usage

_FINDINGS_JSON = '[{"claim":"c","evidence":["e"],"confidence":0.9,"severity":"high","alternatives":[]}]'


class FindingsProvider:
    name = "fake"

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(text=_FINDINGS_JSON, model=request.model, usage=Usage(3, 4), latency_ms=0.0)


class RoleAwareProvider:
    """Raises when the system prompt contains ``fail_keyword``."""

    name = "fake"

    def __init__(self, fail_keyword: str) -> None:
        self._kw = fail_keyword

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        if self._kw in request.messages[0].content:
            raise RuntimeError("boom")
        return ProviderResult(text=_FINDINGS_JSON, model=request.model, usage=Usage(1, 1), latency_ms=0.0)


class SlowProvider:
    name = "fake"

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        await asyncio.sleep(0.2)
        return ProviderResult(text=_FINDINGS_JSON, model=request.model, usage=Usage(1, 1), latency_ms=0.0)


class FlakyProvider:
    name = "fake"

    def __init__(self, fail_times: int) -> None:
        self._remaining = fail_times

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        if self._remaining > 0:
            self._remaining -= 1
            raise RuntimeError("transient")
        return ProviderResult(text=_FINDINGS_JSON, model=request.model, usage=Usage(1, 1), latency_ms=0.0)


def test_merge_is_deterministic_regardless_of_order() -> None:
    a = Finding(agent="architect", claim="x", confidence=0.5, severity="low")
    b = Finding(agent="security", claim="y", confidence=0.9, severity="high")
    c = Finding(agent="qa", claim="z", confidence=0.8, severity="med")
    assert merge_findings([a, b, c]) == merge_findings([c, a, b])
    # high severity first, then med, then low
    assert [f.severity for f in merge_findings([a, b, c])] == ["high", "med", "low"]


def test_merge_dedupes_by_agent_and_claim() -> None:
    f1 = Finding(agent="qa", claim="dup")
    f2 = Finding(agent="qa", claim="dup")
    assert len(merge_findings([f1, f2])) == 1


def test_full_run_succeeds_and_is_deterministic() -> None:
    orch = Orchestrator(FindingsProvider(), "m")
    r1 = asyncio.run(orch.run("review this"))
    r2 = asyncio.run(orch.run("review this"))
    assert r1.succeeded == 5
    assert r1.failed == []
    assert [f.model_dump() for f in r1.merged] == [f.model_dump() for f in r2.merged]
    assert [a.agent for a in r1.agents] == ["architect", "engineer", "qa", "reviewer", "security"]


def test_partial_failure_is_isolated() -> None:
    orch = Orchestrator(RoleAwareProvider("security"), "m", retries=0)
    report = asyncio.run(orch.run("task"))
    assert report.failed == ["security"]
    assert report.succeeded == 4
    assert all(a.status == "error" for a in report.agents if a.agent == "security")


def test_timeout_is_captured() -> None:
    orch = Orchestrator(SlowProvider(), "m", timeout_s=0.05, retries=0)
    report = asyncio.run(orch.run("task"))
    assert report.succeeded == 0
    assert all(a.status == "timeout" for a in report.agents)


def test_retry_recovers_transient_failure() -> None:
    spec = (AgentSpec("solo", "system contract"),)
    orch = Orchestrator(FlakyProvider(fail_times=1), "m", retries=1, agents=spec)
    report = asyncio.run(orch.run("task"))
    assert report.succeeded == 1
    assert report.agents[0].attempts == 2


def test_agent_results_carry_metrics() -> None:
    report = asyncio.run(Orchestrator(FindingsProvider(), "m").run("task"))
    ok = report.agents[0]
    assert isinstance(ok, AgentResult)
    assert ok.tokens_in == 3 and ok.tokens_out == 4
