from __future__ import annotations

import json
import shutil
from pathlib import Path

from tests.fixtures.golden_loader import corpus_path
from typer.testing import CliRunner

from forgeos.adapters.transport.cli.app import app

runner = CliRunner()


def test_scan_reports_and_persists(tmp_path: Path) -> None:
    repo = tmp_path / "medium"
    shutil.copytree(corpus_path("medium"), repo)
    project = tmp_path / "proj"

    result = runner.invoke(
        app, ["scan", "--path", str(repo), "--project", str(project)]
    )
    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["files"] == 4
    assert report["modules"] == 2
    assert report["external_deps"] == 1

    # Graph + profile persisted as snapshots (source of truth).
    assert (project / ".forgeos" / "snapshots" / "nodes.yaml").exists()
    assert (project / ".forgeos" / "snapshots" / "repo_profile.yaml").exists()
