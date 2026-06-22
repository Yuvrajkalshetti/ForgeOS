"""CLI <-> MCP parity (ADR 0007): equivalent read-only tools must match CLI JSON."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from typer.testing import CliRunner

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.adapters.transport.cli.app import app
from forgeos.adapters.transport.mcp import server as mcp
from forgeos.core.memory import MemoryKind, MemoryScope, MemoryService
from forgeos.core.memory.models import Source

runner = CliRunner()


def _seed(project: Path) -> None:
    MemoryService(open_store(project)).add(
        MemoryScope.PROJECT, MemoryKind.FACT, "uses uv", source=Source(type="test")
    )


def test_status_parity(tmp_project: Path) -> None:
    _seed(tmp_project)
    cli = json.loads(runner.invoke(app, ["status", "--project", str(tmp_project)]).stdout)
    tool = asyncio.run(mcp.forgeos_status(str(tmp_project)))
    assert cli == tool


def test_memory_summary_parity(tmp_project: Path) -> None:
    _seed(tmp_project)
    cli = json.loads(
        runner.invoke(app, ["memory", "query", "--project", str(tmp_project)]).stdout
    )
    tool = asyncio.run(mcp.forgeos_memory_summary(project=str(tmp_project)))
    assert cli == tool


def test_skill_list_parity(tmp_project: Path) -> None:
    cli = json.loads(runner.invoke(app, ["skill", "list", "--project", str(tmp_project)]).stdout)
    tool = asyncio.run(mcp.forgeos_skill_list(str(tmp_project)))
    assert cli == tool
