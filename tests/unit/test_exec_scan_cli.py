from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forgeos.adapters.transport.cli.app import app

runner = CliRunner()


def test_exec_scan_reports_symbol_counts(tmp_path: Path) -> None:
    (tmp_path / "m.py").write_text(
        "def f():\n    pass\n\nclass A:\n    def g(self):\n        pass\n", encoding="utf-8"
    )
    result = runner.invoke(
        app, ["exec-scan", "--path", str(tmp_path), "--project", str(tmp_path)]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["functions"] == 1
    assert payload["methods"] == 1
    assert payload["classes"] == 1
    assert payload["defines_edges"] == 3
