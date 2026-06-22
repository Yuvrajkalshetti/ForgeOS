from __future__ import annotations

import asyncio
from pathlib import Path

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.adapters.transport.mcp import server as mcp
from forgeos.catalog import Collections
from forgeos.core.memory import MemoryKind, MemoryScope, MemoryService
from forgeos.core.memory.models import Source
from forgeos.ports.provider import ProviderRequest, ProviderResult, Usage

_RO_COLLECTIONS = [
    Collections.MEMORY,
    Collections.NODES,
    Collections.EDGES,
    Collections.CARDS,
    Collections.PROPOSALS,
    Collections.ADVISORY_SESSIONS,
]
_MENTOR_JSON = '{"kind":"proposal","understanding":"u","recommendation":"r","proposed_plan":["s1"]}'


class _JsonProvider:
    name = "fake"

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(
            text=_MENTOR_JSON, model=request.model, usage=Usage(1, 1), latency_ms=0.0
        )


def _seed_memory(project: Path) -> None:
    MemoryService(open_store(project)).add(
        MemoryScope.PROJECT, MemoryKind.FACT, "uses uv", source=Source(type="test")
    )


def _counts(project: Path) -> dict[str, int]:
    store = open_store(project)
    return {c: len(store.query(c)) for c in _RO_COLLECTIONS}


def test_status_reports_counts(tmp_project: Path) -> None:
    _seed_memory(tmp_project)
    result = asyncio.run(mcp.forgeos_status(str(tmp_project)))
    assert result["initialized"] is True
    assert result["counts"]["memory"] == 1


def test_doctor_runs_read_only(tmp_project: Path) -> None:
    result = asyncio.run(mcp.forgeos_doctor(str(tmp_project)))
    assert "ok" in result
    assert any(c["name"] == "python" for c in result["checks"])


def test_memory_summary_returns_records(tmp_project: Path) -> None:
    _seed_memory(tmp_project)
    records = asyncio.run(mcp.forgeos_memory_summary(project=str(tmp_project)))
    assert len(records) == 1
    assert records[0]["content"] == "uses uv"


def test_skill_and_graph_tools_handle_missing(tmp_project: Path) -> None:
    assert asyncio.run(mcp.forgeos_skill_list(str(tmp_project))) == []
    assert "error" in asyncio.run(mcp.forgeos_skill_show("nope", str(tmp_project)))
    assert "error" in asyncio.run(mcp.forgeos_graph_summary("nope", project=str(tmp_project)))


def test_read_only_tools_do_not_mutate(tmp_project: Path) -> None:
    _seed_memory(tmp_project)
    before = _counts(tmp_project)
    asyncio.run(mcp.forgeos_status(str(tmp_project)))
    asyncio.run(mcp.forgeos_doctor(str(tmp_project)))
    asyncio.run(mcp.forgeos_skill_list(str(tmp_project)))
    asyncio.run(mcp.forgeos_skill_show("x", str(tmp_project)))
    asyncio.run(mcp.forgeos_graph_summary("x", project=str(tmp_project)))
    asyncio.run(mcp.forgeos_memory_summary(project=str(tmp_project)))
    assert _counts(tmp_project) == before


def test_mentor_returns_error_without_provider(tmp_project: Path, monkeypatch) -> None:
    def _raise(*a, **k):
        raise mcp.ProviderUnavailable("no key")

    monkeypatch.setattr(mcp, "build_provider", _raise)
    result = asyncio.run(mcp.forgeos_mentor("review", ground=False, project=str(tmp_project)))
    assert result["error"] == "no key"


def test_mentor_runs_with_fake_provider(tmp_project: Path, monkeypatch) -> None:
    monkeypatch.setattr(mcp, "build_provider", lambda *a, **k: _JsonProvider())
    result = asyncio.run(mcp.forgeos_mentor("review", ground=False, project=str(tmp_project)))
    assert result["session_id"]
    assert result["recommendation"]["recommendation"] == "r"
    assert result["grounding"] is None
