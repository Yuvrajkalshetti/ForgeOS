"""``forge learn`` commands: review, approve, reject, commit.

Transport adapter over :class:`LearningService`. Every transition is human-gated —
``--actor`` is required and recorded in provenance. ``commit`` "Becomes a Skill"
(creates a Skill graph node); inspect it with ``forge skill``.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from forgeos.adapters.storage.sqlite import SnapshotStore
from forgeos.core.graph import GraphStore
from forgeos.core.learning import InvalidTransition, LearningService

learn_app = typer.Typer(
    help="Human-gated learning: review/approve/reject/commit.", no_args_is_help=True
)

_ACTOR = typer.Option(..., "--actor", help="human making this decision (recorded in provenance)")
_NOTE = typer.Option("", "--note", help="optional rationale recorded in provenance")


def _service(project: Path) -> LearningService:
    db = project / ".forgeos" / "cache" / "forge.sqlite"
    db.parent.mkdir(parents=True, exist_ok=True)
    store = SnapshotStore.open(project / ".forgeos" / "snapshots", db)
    return LearningService(store, GraphStore(store))


def _emit(payload: object) -> None:
    typer.echo(json.dumps(payload, indent=2))


def _run(action: str, project: Path, proposal_id: str, actor: str, note: str) -> None:
    svc = _service(project)
    fn = {"approve": svc.approve, "reject": svc.reject, "commit": svc.commit}[action]
    try:
        proposal = fn(proposal_id, actor=actor, note=note)
    except KeyError:
        _emit({"error": f"proposal not found: {proposal_id}"})
        raise typer.Exit(code=1) from None
    except InvalidTransition as exc:
        _emit({"error": str(exc)})
        raise typer.Exit(code=1) from exc
    _emit(proposal.model_dump(mode="json"))


@learn_app.command("review")
def review(project: Path = Path()) -> None:
    """List proposals awaiting a human decision (newest first)."""
    pending = _service(project).review()
    _emit([p.model_dump(mode="json") for p in pending])


@learn_app.command("approve")
def approve(
    proposal_id: str, actor: str = _ACTOR, note: str = _NOTE, project: Path = Path()
) -> None:
    """Approve a proposal (proposed → approved)."""
    _run("approve", project, proposal_id, actor, note)


@learn_app.command("reject")
def reject(
    proposal_id: str, actor: str = _ACTOR, note: str = _NOTE, project: Path = Path()
) -> None:
    """Reject a proposal (proposed/approved → rejected)."""
    _run("reject", project, proposal_id, actor, note)


@learn_app.command("commit")
def commit(
    proposal_id: str, actor: str = _ACTOR, note: str = _NOTE, project: Path = Path()
) -> None:
    """Commit an approved proposal — "Become a Skill" (approved → committed)."""
    _run("commit", project, proposal_id, actor, note)
