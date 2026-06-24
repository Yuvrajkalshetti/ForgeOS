from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forgeos.adapters.transport.cli.app import app

runner = CliRunner()


def test_sync_builds_all_graphs(tmp_path: Path) -> None:
    (tmp_path / "m.py").write_text(
        "class A:\n    def w(self):\n        self.x = 1\n\ndef f():\n    pass\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["sync", "--path", str(tmp_path), "--project", str(tmp_path)])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "graph" in payload
    assert "exec" in payload
    assert "dataflow" in payload
    assert payload["exec"]["functions"] >= 1
