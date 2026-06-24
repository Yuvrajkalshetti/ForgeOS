"""The ``forge`` CLI.

P0 wires the transport seam and two read-only commands (``version``,
``config show``). Later phases attach ``scan``, ``compress``, ``memory``,
``graph``, ``context``, ``tokens``, ``agent`` and ``provider`` against the same
service layer the MCP transport will use, preserving CLI/MCP parity.
"""

from __future__ import annotations

import json

import typer

from forgeos import __version__
from forgeos.adapters.transport.cli.agent import agent_app
from forgeos.adapters.transport.cli.audit import audit as audit_command
from forgeos.adapters.transport.cli.compress import compress_app
from forgeos.adapters.transport.cli.context import context_app
from forgeos.adapters.transport.cli.doctor import doctor_cmd
from forgeos.adapters.transport.cli.exec_scan import exec_scan
from forgeos.adapters.transport.cli.graph import graph_app
from forgeos.adapters.transport.cli.learn import learn_app
from forgeos.adapters.transport.cli.memory import memory_app
from forgeos.adapters.transport.cli.mentor import mentor as mentor_command
from forgeos.adapters.transport.cli.portability import (
    backup_cmd,
    export_cmd,
    import_cmd,
    init_cmd,
)
from forgeos.adapters.transport.cli.provider import provider_app
from forgeos.adapters.transport.cli.scan import scan as scan_command
from forgeos.adapters.transport.cli.skill import skill_app
from forgeos.adapters.transport.cli.status import status_cmd
from forgeos.adapters.transport.cli.sync import sync as sync_command
from forgeos.adapters.transport.cli.tokens import tokens_app
from forgeos.adapters.transport.cli.wizard import wizard_cmd
from forgeos.config.loader import load_config
from forgeos.observability import configure_logging, new_request_id

app = typer.Typer(
    name="forge",
    help="ForgeOS — local-first AI Operating System.",
    no_args_is_help=True,
    add_completion=False,
)

config_app = typer.Typer(help="Inspect ForgeOS configuration.", no_args_is_help=True)
app.add_typer(config_app, name="config")
app.add_typer(memory_app, name="memory")
app.add_typer(graph_app, name="graph")
app.add_typer(tokens_app, name="tokens")
app.add_typer(context_app, name="context")
app.add_typer(compress_app, name="compress")
app.add_typer(provider_app, name="provider")
app.add_typer(agent_app, name="agent")
app.add_typer(learn_app, name="learn")
app.add_typer(skill_app, name="skill")
app.command(name="scan")(scan_command)
app.command(name="exec-scan")(exec_scan)
app.command(name="sync")(sync_command)
app.command(name="mentor")(mentor_command)
app.command(name="audit")(audit_command)
app.command(name="export")(export_cmd)
app.command(name="import")(import_cmd)
app.command(name="backup")(backup_cmd)
app.command(name="init")(init_cmd)
app.command(name="doctor")(doctor_cmd)
app.command(name="status")(status_cmd)
app.command(name="wizard")(wizard_cmd)


@app.command()
def version() -> None:
    """Print the ForgeOS version."""
    typer.echo(__version__)


@config_app.command("show")
def config_show() -> None:
    """Print the effective layered configuration as JSON."""
    config = load_config()
    typer.echo(json.dumps(config.model_dump(by_alias=True), indent=2, default=str))


def main() -> None:
    """Console-script entrypoint (``forge``)."""
    configure_logging()
    new_request_id()
    app()


if __name__ == "__main__":
    main()
