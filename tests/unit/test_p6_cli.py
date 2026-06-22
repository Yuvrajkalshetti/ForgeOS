from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forgeos.adapters.transport.cli import agent as agent_module
from forgeos.adapters.transport.cli._shared import open_store
from forgeos.adapters.transport.cli.app import app
from forgeos.core.provider_intel import StatsRecorder
from forgeos.ports.provider import ProviderRequest, ProviderResult, Usage

runner = CliRunner()

_FINDINGS = '[{"claim":"c","evidence":["e"],"confidence":0.9,"severity":"high","alternatives":[]}]'


class _FakeProvider:
    name = "fake"

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(text=_FINDINGS, model=request.model, usage=Usage(2, 3), latency_ms=0.0)


def test_provider_use_sets_default(tmp_path: Path) -> None:
    result = runner.invoke(app, ["provider", "use", "ollama", "--project", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["default"] == "ollama"


def test_provider_stats_reports_scorecards(tmp_path: Path) -> None:
    StatsRecorder(open_store(tmp_path)).record(
        "claude", "m", tokens_in=10, tokens_out=5, latency_ms=12.0, success=True
    )
    result = runner.invoke(app, ["provider", "stats", "--project", str(tmp_path)])
    assert result.exit_code == 0
    cards = json.loads(result.stdout)
    assert cards[0]["provider"] == "claude"
    assert cards[0]["calls"] == 1


def test_agent_run_without_provider_fails_gracefully(tmp_path: Path) -> None:
    # Default provider is claude; with no API key the run fails cleanly (isolation).
    result = runner.invoke(
        app, ["agent", "run", "review", "--project", str(tmp_path)],
        env={"ANTHROPIC_API_KEY": ""},
    )
    assert result.exit_code == 1
    assert "routing" in result.stdout  # routing transparency printed first
    assert "API key" in result.stdout


def test_core_still_works_without_provider(tmp_path: Path) -> None:
    # Provider isolation: a core command needs no provider and must succeed.
    result = runner.invoke(
        app, ["memory", "add", "works offline", "--project", str(tmp_path)],
        env={"ANTHROPIC_API_KEY": ""},
    )
    assert result.exit_code == 0
    assert result.stdout.strip().startswith("mem_")


def test_agent_run_success_with_injected_provider(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(agent_module, "build_provider", lambda *a, **k: _FakeProvider())
    result = runner.invoke(app, ["agent", "run", "review this", "--project", str(tmp_path)])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["routing"]["selected"] == "claude"
    assert payload["report"]["succeeded"] == 5
    assert payload["report"]["merged"][0]["severity"] == "high"
