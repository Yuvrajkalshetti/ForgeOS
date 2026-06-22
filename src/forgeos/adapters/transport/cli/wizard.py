"""``forge wizard`` / ``forgeos wizard`` — first-run navigation guide.

A guidance-only walkthrough of the happy path for new users. Non-interactive (prints
the exact commands to run, in order) so it is safe in scripts/CI and never blocks.
Introduces no capability — it only narrates existing commands.
"""

from __future__ import annotations

from pathlib import Path

import typer

_STEPS = [
    ("forgeos init", "Create this project's .forgeos workspace (idempotent)."),
    ("forgeos doctor", "Check setup: provider, credentials, Python — fix anything FAIL."),
    ("forgeos scan", "Ingest the repository into the knowledge graph (provider-free)."),
    ("forgeos compress run --bulk", "Turn scanned code into compact knowledge cards."),
    ("forgeos mentor \"<your question>\"", "Ask for a grounded implementation strategy."),
    ("forgeos status", "See what ForgeOS now knows about this project."),
]


def wizard_cmd(project: Path = Path()) -> None:
    """Print an ordered, copy-pasteable getting-started walkthrough."""
    typer.echo("ForgeOS — getting started\n")
    for i, (cmd, why) in enumerate(_STEPS, start=1):
        typer.echo(f"  {i}. {cmd}")
        typer.echo(f"       {why}")
    typer.echo(
        "\nTip: provider-backed steps (mentor/audit/agent) need a configured provider — "
        "run `forgeos doctor` first. Set Claude via `export ANTHROPIC_API_KEY=...`, "
        "or `forgeos provider use ollama` for a local model."
    )
