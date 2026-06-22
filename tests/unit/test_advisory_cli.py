from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forgeos.adapters.transport.cli import audit as audit_module
from forgeos.adapters.transport.cli import mentor as mentor_module
from forgeos.adapters.transport.cli.app import app
from forgeos.ports.provider import ProviderRequest, ProviderResult, Usage

runner = CliRunner()

_MENTOR_JSON = (
    '{"kind":"proposal","understanding":"u","assumptions":[],"challenges":[],'
    '"gaps":[],"alternatives":[],"recommendation":"r","proposed_plan":["s1"],'
    '"confidence":"high"}'
)
_AUDIT_JSON = (
    '{"evidence_review":"e","architecture_compliance":"ok","test_coverage":"ok",'
    '"risks":[],"violations":[],"recommendation":"accept","confidence":"low"}'
)


class _JsonProvider:
    name = "fake"

    def __init__(self, reply: str) -> None:
        self._reply = reply

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(text=self._reply, model=request.model, usage=Usage(1, 1), latency_ms=0.0)


def test_mentor_graceful_without_provider(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["mentor", "add caching", "--project", str(tmp_path)],
        env={"ANTHROPIC_API_KEY": ""},
    )
    assert result.exit_code == 1
    assert "API key" in result.stdout


def test_mentor_success_with_injected_provider(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(mentor_module, "build_provider", lambda *a, **k: _JsonProvider(_MENTOR_JSON))
    result = runner.invoke(
        app, ["mentor", "add caching", "--json", "--project", str(tmp_path)]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["recommendation"]["recommendation"] == "r"
    assert payload["session_id"].startswith("asess_")


def test_audit_success_with_injected_provider(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(audit_module, "build_provider", lambda *a, **k: _JsonProvider(_AUDIT_JSON))
    result = runner.invoke(
        app, ["audit", "the auth module", "--json", "--project", str(tmp_path)]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["finding"]["recommendation"] == "accept"
