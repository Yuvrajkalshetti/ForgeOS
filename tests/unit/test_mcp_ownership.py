from __future__ import annotations

import asyncio
from pathlib import Path

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.adapters.transport.mcp import server as mcp
from forgeos.core.exec_intel import ExecGraphStore, ExecIntelEngine


def _prepare(tmp_path: Path) -> None:
    (tmp_path / ".forgeos").mkdir(exist_ok=True)
    (tmp_path / ".forgeos" / "ownership.yaml").write_text(
        "rules:\n  - match: {path: 'exec.py'}\n    domain: Execution Domain\n    criticality: P0\n",
        encoding="utf-8",
    )
    (tmp_path / "exec.py").write_text("def place_order():\n    pass\n", encoding="utf-8")
    ExecIntelEngine(ExecGraphStore(open_store(tmp_path))).scan(tmp_path)


def test_runtime_owner_tool(tmp_path: Path) -> None:
    _prepare(tmp_path)
    res = asyncio.run(mcp.forgeos_runtime_owner("func:exec.py#place_order", project=str(tmp_path)))
    assert res["declared_owner"] == "Execution Domain"
    assert res["criticality"] == "P0"
    assert "observed_owner" in res
    assert "agreement" in res


def test_runtime_summary_tool(tmp_path: Path) -> None:
    _prepare(tmp_path)
    res = asyncio.run(mcp.forgeos_runtime_summary("func:exec.py#place_order", project=str(tmp_path)))
    assert res["declared_owner"] == "Execution Domain"
    assert "consumers" in res
    assert "dependencies" in res


def test_missing_symbol_errors(tmp_path: Path) -> None:
    _prepare(tmp_path)
    res = asyncio.run(mcp.forgeos_runtime_owner("nope", project=str(tmp_path)))
    assert "error" in res
