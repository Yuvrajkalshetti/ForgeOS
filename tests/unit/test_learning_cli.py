"""CLI surface for the Learning loop: ``forge learn`` + ``forge skill``.

End-to-end through the snapshot store: emit a proposal, then drive it through the
human-gated transitions and confirm "Become a Skill" is inspectable via ``forge skill``.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.adapters.transport.cli.app import app
from forgeos.core.learning import emit_proposal

runner = CliRunner()


def _store(project: Path) -> SnapshotStore:
    db = project / ".forgeos" / "cache" / "forge.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    return SnapshotStore.open(project / ".forgeos" / "snapshots", db)


def _seed(project: Path, name: str = "retry-with-backoff") -> str:
    proposal = emit_proposal(
        _store(project), kind="skill.candidate", payload={"name": name}, evidence=["seen 3x"]
    )
    return proposal.id


# -- learn review ----------------------------------------------------------------
def test_learn_review_lists_pending(tmp_path: Path) -> None:
    _seed(tmp_path)
    result = runner.invoke(app, ["learn", "review", "--project", str(tmp_path)])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert len(payload) == 1
    assert payload[0]["status"] == "proposed"


# -- approve / reject ------------------------------------------------------------
def test_learn_approve_records_provenance(tmp_path: Path) -> None:
    pid = _seed(tmp_path)
    result = runner.invoke(
        app, ["learn", "approve", pid, "--actor", "yuvraj", "--note", "ok", "--project", str(tmp_path)]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "approved"
    assert payload["provenance"][0]["actor"] == "yuvraj"
    # no longer pending
    review = runner.invoke(app, ["learn", "review", "--project", str(tmp_path)])
    assert json.loads(review.stdout) == []


def test_learn_reject(tmp_path: Path) -> None:
    pid = _seed(tmp_path)
    result = runner.invoke(
        app, ["learn", "reject", pid, "--actor", "yuvraj", "--project", str(tmp_path)]
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)["status"] == "rejected"


# -- commit "Become a Skill" -----------------------------------------------------
def test_learn_commit_creates_skill_then_inspectable(tmp_path: Path) -> None:
    pid = _seed(tmp_path, name="cache-keys")
    assert runner.invoke(
        app, ["learn", "approve", pid, "--actor", "yuvraj", "--project", str(tmp_path)]
    ).exit_code == 0
    commit = runner.invoke(
        app, ["learn", "commit", pid, "--actor", "yuvraj", "--project", str(tmp_path)]
    )
    assert commit.exit_code == 0
    committed = json.loads(commit.stdout)
    assert committed["status"] == "committed"
    skill_id = committed["skill_id"]
    assert skill_id

    listing = runner.invoke(app, ["skill", "list", "--project", str(tmp_path)])
    assert listing.exit_code == 0
    skills = json.loads(listing.stdout)
    assert [s["label"] for s in skills] == ["cache-keys"]

    show = runner.invoke(app, ["skill", "show", skill_id, "--project", str(tmp_path)])
    assert show.exit_code == 0
    node = json.loads(show.stdout)
    assert node["props"]["proposal_id"] == pid  # lineage back to the proposal


def test_learn_commit_without_approval_fails(tmp_path: Path) -> None:
    pid = _seed(tmp_path)
    result = runner.invoke(
        app, ["learn", "commit", pid, "--actor", "yuvraj", "--project", str(tmp_path)]
    )
    assert result.exit_code == 1
    assert "commit" in result.stdout.lower()


def test_learn_approve_unknown_id_fails(tmp_path: Path) -> None:
    _store(tmp_path)
    result = runner.invoke(
        app, ["learn", "approve", "prop_nope", "--actor", "yuvraj", "--project", str(tmp_path)]
    )
    assert result.exit_code == 1


# -- skill list / show -----------------------------------------------------------
def test_skill_list_empty(tmp_path: Path) -> None:
    _store(tmp_path)
    result = runner.invoke(app, ["skill", "list", "--project", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


def test_skill_show_unknown_fails(tmp_path: Path) -> None:
    _store(tmp_path)
    result = runner.invoke(app, ["skill", "show", "ghost", "--project", str(tmp_path)])
    assert result.exit_code == 1
    assert "not found" in result.stdout
