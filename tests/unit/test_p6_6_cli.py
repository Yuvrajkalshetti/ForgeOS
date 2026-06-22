from __future__ import annotations

import json
import shutil
from pathlib import Path

from tests.fixtures.golden_loader import corpus_path
from typer.testing import CliRunner

from forgeos.adapters.transport.cli import mentor as mentor_module
from forgeos.adapters.transport.cli.app import app
from forgeos.ports.provider import ProviderRequest, ProviderResult, Usage

runner = CliRunner()
_MENTOR_JSON = '{"kind":"proposal","understanding":"u","recommendation":"r","proposed_plan":["s1"]}'


class _JsonProvider:
    name = "fake"

    async def generate(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(text=_MENTOR_JSON, model=request.model, usage=Usage(1, 1), latency_ms=0.0)


def _scanned_and_compressed(tmp_path: Path) -> Path:
    repo = tmp_path / "medium"
    shutil.copytree(corpus_path("medium"), repo)
    project = tmp_path / "proj"
    assert runner.invoke(app, ["scan", "--path", str(repo), "--project", str(project)]).exit_code == 0
    assert runner.invoke(app, ["compress", "run", "--bulk", "--project", str(project)]).exit_code == 0
    return project


def test_mentor_cli_grounds_in_forgeos_knowledge(tmp_path: Path, monkeypatch) -> None:
    project = _scanned_and_compressed(tmp_path)
    monkeypatch.setattr(mentor_module, "build_provider", lambda *a, **k: _JsonProvider())
    result = runner.invoke(
        app, ["mentor", "review module", "--target", "pkg_b", "--json", "--project", str(project)]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["grounding"] is not None
    kinds = {i["kind"] for i in payload["grounding"]["items"]}
    assert "card" in kinds  # cards-first grounding from existing knowledge
    assert payload["recommendation"]["grounding_refs"]  # refs recorded for lineage


def test_mentor_cli_no_ground_flag(tmp_path: Path, monkeypatch) -> None:
    project = _scanned_and_compressed(tmp_path)
    monkeypatch.setattr(mentor_module, "build_provider", lambda *a, **k: _JsonProvider())
    result = runner.invoke(
        app, ["mentor", "review", "--no-ground", "--json", "--project", str(project)]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["grounding"] is None
    assert payload["recommendation"]["grounding_refs"] == []
