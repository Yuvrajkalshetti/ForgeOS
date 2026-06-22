from __future__ import annotations

import json
import shutil
from pathlib import Path

from tests.fixtures.golden_loader import corpus_path
from typer.testing import CliRunner

from forgeos.adapters.transport.cli.app import app

runner = CliRunner()


def _scanned_project(tmp_path: Path) -> Path:
    repo = tmp_path / "medium"
    shutil.copytree(corpus_path("medium"), repo)
    project = tmp_path / "proj"
    assert runner.invoke(
        app, ["scan", "--path", str(repo), "--project", str(project)]
    ).exit_code == 0
    return project


def test_compress_bulk_then_context_and_tokens(tmp_path: Path) -> None:
    project = _scanned_project(tmp_path)

    # compress all files (deterministic, provider-free)
    comp = runner.invoke(app, ["compress", "run", "--bulk", "--project", str(project)])
    assert comp.exit_code == 0
    assert json.loads(comp.stdout)["cards"]

    # find a module node to assemble around
    modules = runner.invoke(app, ["graph", "query", "pkg_b", "--project", str(project)])
    assert modules.exit_code == 0

    ctx = runner.invoke(
        app, ["context", "build", "pkg_b", "--budget", "5000", "--project", str(project)]
    )
    assert ctx.exit_code == 0
    bundle = json.loads(ctx.stdout)
    assert bundle["total_tokens"] <= 5000
    assert "manifest" in bundle

    tokens = runner.invoke(app, ["tokens", "report", "--project", str(project)])
    assert tokens.exit_code == 0
    report = json.loads(tokens.stdout)
    assert report["events"] >= 1
    assert "compression_ratio" in report


def test_context_build_budget_enforced_via_cli(tmp_path: Path) -> None:
    project = _scanned_project(tmp_path)
    runner.invoke(app, ["compress", "run", "--bulk", "--project", str(project)])
    result = runner.invoke(
        app, ["context", "build", "pkg_a", "--budget", "1", "--project", str(project)]
    )
    assert result.exit_code == 0
    bundle = json.loads(result.stdout)
    assert bundle["total_tokens"] <= 1
