"""``forge provider`` commands: stats, use."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
import yaml

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.config.loader import load_config
from forgeos.core.provider_intel import StatsRecorder

provider_app = typer.Typer(help="Provider stats and selection.", no_args_is_help=True)


@provider_app.command("stats")
def stats(project: Path = Path()) -> None:
    """Print per-provider scorecards as JSON."""
    recorder = StatsRecorder(open_store(project))
    cards = [c.model_dump() for c in recorder.scorecards()]
    typer.echo(json.dumps(cards, indent=2))


@provider_app.command("use")
def use(name: str, project: Path = Path()) -> None:
    """Set the default provider in the project config."""
    config_path = project / ".forgeos" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {}
    if config_path.exists():
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    data.setdefault("providers", {})["default"] = name
    config_path.write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")
    effective = load_config(project_dir=project).providers.default
    typer.echo(json.dumps({"default": effective}))
