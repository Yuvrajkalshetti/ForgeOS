from __future__ import annotations

import json

from typer.testing import CliRunner

from forgeos import __version__
from forgeos.adapters.transport.cli.app import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_config_show_outputs_valid_json() -> None:
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["providers"]["default"] in {"claude", "ollama"}


def test_no_args_shows_help() -> None:
    # `no_args_is_help` prints usage and exits with Click's usage code (2).
    result = runner.invoke(app, [])
    assert result.exit_code == 2
    assert "Usage" in result.output
