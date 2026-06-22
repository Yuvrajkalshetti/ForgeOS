"""Async agent orchestrator.

Runs agents concurrently, bounded by a semaphore (global + per-provider limits),
with per-call timeout, retry-with-backoff, and failure isolation: a failing agent
becomes a non-``ok`` result rather than aborting the run. Results are gathered in
agent order and merged deterministically, so the merged output is reproducible.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Sequence

from pydantic import BaseModel, Field

from forgeos.core.orchestrator.agents import DEFAULT_AGENTS, AgentSpec, Finding
from forgeos.core.orchestrator.merge import merge_findings
from forgeos.ports.provider import Message, ProviderPort, ProviderRequest


class AgentResult(BaseModel):
    """The outcome of one agent's run."""

    agent: str
    status: str  # ok | error | timeout
    findings: list[Finding] = Field(default_factory=list)
    error: str = ""
    attempts: int = 0
    latency_ms: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0


class OrchestratorReport(BaseModel):
    """Aggregated multi-agent run."""

    task: str
    agents: list[AgentResult] = Field(default_factory=list)
    merged: list[Finding] = Field(default_factory=list)
    succeeded: int = 0
    failed: list[str] = Field(default_factory=list)


def _parse_findings(text: str, agent: str) -> list[Finding]:
    raw = json.loads(text)
    if not isinstance(raw, list):
        raise ValueError("expected a JSON array of findings")
    return [
        Finding(
            agent=agent,
            claim=str(item["claim"]),
            evidence=list(item.get("evidence", [])),
            confidence=float(item.get("confidence", 0.5)),
            severity=str(item.get("severity", "low")),
            alternatives=list(item.get("alternatives", [])),
        )
        for item in raw
    ]


class Orchestrator:
    """Coordinate a fixed set of agents over a single provider."""

    def __init__(
        self,
        provider: ProviderPort,
        model: str,
        *,
        global_limit: int = 5,
        per_provider_limit: int | None = None,
        timeout_s: float = 30.0,
        retries: int = 1,
        backoff_s: float = 0.0,
        agents: Sequence[AgentSpec] = DEFAULT_AGENTS,
    ) -> None:
        self._provider = provider
        self._model = model
        self._limit = max(1, min(global_limit, per_provider_limit or global_limit))
        self._timeout_s = timeout_s
        self._retries = retries
        self._backoff_s = backoff_s
        self._agents = tuple(agents)

    async def run(self, task: str, context: str = "") -> OrchestratorReport:
        """Run all agents concurrently and return a merged, deterministic report."""
        semaphore = asyncio.Semaphore(self._limit)
        results = await asyncio.gather(
            *(self._run_agent(agent, task, context, semaphore) for agent in self._agents)
        )
        ok_findings = [f for r in results if r.status == "ok" for f in r.findings]
        return OrchestratorReport(
            task=task,
            agents=sorted(results, key=lambda r: r.agent),
            merged=merge_findings(ok_findings),
            succeeded=sum(1 for r in results if r.status == "ok"),
            failed=sorted(r.agent for r in results if r.status != "ok"),
        )

    async def _run_agent(
        self, agent: AgentSpec, task: str, context: str, semaphore: asyncio.Semaphore
    ) -> AgentResult:
        request = ProviderRequest(
            messages=[
                Message("system", agent.system_prompt),
                Message("user", f"{task}\n\n{context}".strip()),
            ],
            model=self._model,
        )
        status, error = "error", ""
        async with semaphore:
            for attempt in range(self._retries + 1):
                started = time.perf_counter()
                try:
                    result = await asyncio.wait_for(
                        self._provider.generate(request), self._timeout_s
                    )
                    findings = _parse_findings(result.text, agent.name)
                    return AgentResult(
                        agent=agent.name, status="ok", findings=findings,
                        attempts=attempt + 1,
                        latency_ms=(time.perf_counter() - started) * 1000,
                        tokens_in=result.usage.input_tokens,
                        tokens_out=result.usage.output_tokens,
                    )
                except TimeoutError:
                    status, error = "timeout", "provider call timed out"
                except Exception as exc:  # isolate: capture, do not abort the run
                    status, error = "error", f"{type(exc).__name__}: {exc}"
                if attempt < self._retries:
                    await asyncio.sleep(self._backoff_s)
        return AgentResult(
            agent=agent.name, status=status, error=error, attempts=self._retries + 1
        )
