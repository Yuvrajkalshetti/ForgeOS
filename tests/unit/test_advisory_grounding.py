from __future__ import annotations

import asyncio
import datetime

from forgeos.core.advisory import Auditor, Mentor
from forgeos.core.context_assembly.models import ContextBundle, ContextItem
from forgeos.core.graph import GraphStore
from forgeos.ports.provider import ProviderRequest, ProviderResult, Usage
from forgeos.testing.fakes import InMemoryStorage

T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
_MENTOR_JSON = '{"kind":"proposal","understanding":"u","recommendation":"r","proposed_plan":[]}'
_AUDIT_JSON = '{"evidence_review":"e","recommendation":"ok","risks":[],"violations":[]}'


class _CapturingProvider:
    name = "fake"

    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.last_user = ""

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        self.last_user = request.messages[1].content
        return ProviderResult(text=self._reply, model=request.model, usage=Usage(1, 1), latency_ms=0.0)


def _bundle() -> ContextBundle:
    return ContextBundle(
        target="auth",
        items=[
            ContextItem(ref="card:File:f1", kind="card", content="auth module purpose",
                        tokens=5, raw_tokens=100, tier=0, order=0),
        ],
        total_tokens=5,
    )


def test_mentor_consumes_grounding_in_prompt_and_records_refs() -> None:
    provider = _CapturingProvider(_MENTOR_JSON)
    graph = GraphStore(InMemoryStorage(), clock=lambda: T0)
    rec = asyncio.run(provider_advise(provider, graph))
    assert "auth module purpose" in provider.last_user  # grounding reached the LLM
    assert "## Grounding" in provider.last_user
    assert rec.grounding_refs == ["card:File:f1"]


async def provider_advise(provider: _CapturingProvider, graph: GraphStore):
    return await Mentor(provider, graph, clock=lambda: T0).advise(
        "add caching", model="m", grounding=_bundle()
    )


def test_auditor_consumes_grounding_in_prompt_and_records_refs() -> None:
    provider = _CapturingProvider(_AUDIT_JSON)
    graph = GraphStore(InMemoryStorage(), clock=lambda: T0)
    finding = asyncio.run(
        Auditor(provider, graph, clock=lambda: T0).audit("auth", model="m", grounding=_bundle())
    )
    assert "auth module purpose" in provider.last_user
    assert finding.grounding_refs == ["card:File:f1"]


def test_advisors_work_without_grounding() -> None:
    provider = _CapturingProvider(_MENTOR_JSON)
    graph = GraphStore(InMemoryStorage(), clock=lambda: T0)
    rec = asyncio.run(Mentor(provider, graph, clock=lambda: T0).advise("x", model="m"))
    assert rec.grounding_refs == []
    assert "## Grounding" not in provider.last_user
