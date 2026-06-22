"""V1.1 usability layer: doctor, status, console alias, init guidance, wizard.

Thin UX surfaces only — no core/schema/storage changes. Each command is read-only or
guidance-only and routes through the same services/stores as the rest of the CLI.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from typer.testing import CliRunner

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.adapters.transport.cli.app import app
from forgeos.core.learning import emit_proposal

runner = CliRunner()
ROOT = Path(__file__).resolve().parents[2]


def _store(project: Path) -> SnapshotStore:
    db = project / ".forgeos" / "cache" / "forge.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    return SnapshotStore.open(project / ".forgeos" / "snapshots", db)


# -- console alias ----------------------------------------------------------------
def test_pyproject_declares_both_console_scripts() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = data["project"]["scripts"]
    assert "forge" in scripts and "forgeos" in scripts  # retain forge for compatibility
    assert scripts["forge"] == scripts["forgeos"]  # same entrypoint


# -- improved init guidance -------------------------------------------------------
def test_init_emits_next_steps(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "--project", str(tmp_path)])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["created"] is True  # existing contract preserved
    assert payload["next_steps"]  # new: non-empty guidance
    assert any("doctor" in s for s in payload["next_steps"])


# -- doctor -----------------------------------------------------------------------
def test_doctor_healthy_with_ollama(tmp_path: Path) -> None:
    runner.invoke(app, ["init", "--project", str(tmp_path)])
    runner.invoke(app, ["provider", "use", "ollama", "--project", str(tmp_path)])
    result = runner.invoke(app, ["doctor", "--project", str(tmp_path)])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert all(c["status"] in ("OK", "INFO") for c in payload["checks"])


def test_doctor_uninitialized_fails(tmp_path: Path) -> None:
    result = runner.invoke(app, ["doctor", "--project", str(tmp_path / "nope")])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert any(c["name"] == "initialized" and c["status"] == "FAIL" for c in payload["checks"])
    assert any("init" in c["detail"].lower() for c in payload["checks"])


def test_doctor_flags_missing_claude_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    runner.invoke(app, ["init", "--project", str(tmp_path)])  # default provider = claude
    result = runner.invoke(app, ["doctor", "--project", str(tmp_path)])
    payload = json.loads(result.stdout)
    cred = next(c for c in payload["checks"] if c["name"] == "credentials")
    assert cred["status"] == "FAIL"
    assert "ANTHROPIC_API_KEY" in cred["detail"]
    assert result.exit_code == 1


# -- status -----------------------------------------------------------------------
def test_status_reports_counts(tmp_path: Path) -> None:
    runner.invoke(app, ["init", "--project", str(tmp_path)])
    store = _store(tmp_path)
    store.put("memory", "m1", {"content": "x"})
    emit_proposal(store, kind="k", payload={})
    result = runner.invoke(app, ["status", "--project", str(tmp_path)])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["initialized"] is True
    assert payload["counts"]["memory"] == 1
    assert payload["counts"]["proposals"] == 1
    assert payload["provider"]  # default present


# -- first-run navigation wizard --------------------------------------------------
def test_wizard_prints_navigation(tmp_path: Path) -> None:
    result = runner.invoke(app, ["wizard", "--project", str(tmp_path)])
    assert result.exit_code == 0
    out = result.stdout.lower()
    for kw in ("init", "doctor", "scan", "mentor"):
        assert kw in out
