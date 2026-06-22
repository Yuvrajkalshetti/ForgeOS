from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forgeos.adapters.transport.cli.app import app

runner = CliRunner()


def test_memory_add_and_query_round_trip(tmp_path: Path) -> None:
    add = runner.invoke(
        app,
        ["memory", "add", "uses uv", "--scope", "project", "--project", str(tmp_path)],
    )
    assert add.exit_code == 0
    record_id = add.stdout.strip()
    assert record_id.startswith("mem_")

    query = runner.invoke(app, ["memory", "query", "--project", str(tmp_path)])
    assert query.exit_code == 0
    records = json.loads(query.stdout)
    assert len(records) == 1
    assert records[0]["content"] == "uses uv"


def test_memory_persists_to_snapshot(tmp_path: Path) -> None:
    runner.invoke(app, ["memory", "add", "fact one", "--project", str(tmp_path)])
    snapshot = tmp_path / ".forgeos" / "snapshots" / "memory.yaml"
    assert snapshot.exists()


def test_memory_gc_reports(tmp_path: Path) -> None:
    runner.invoke(app, ["memory", "add", "fact", "--project", str(tmp_path)])
    gc = runner.invoke(app, ["memory", "gc", "--project", str(tmp_path)])
    assert gc.exit_code == 0
    report = json.loads(gc.stdout)
    assert "expired_session" in report
    assert "consolidation_proposals" in report
