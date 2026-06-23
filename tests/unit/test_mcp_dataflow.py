from __future__ import annotations

import asyncio
from pathlib import Path

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.adapters.transport.mcp import server as mcp
from forgeos.core.dataflow_intel import DataFlowEngine, DataFlowStore


def _prepare(tmp_path: Path) -> None:
    (tmp_path / "m.py").write_text(
        "class A:\n"
        "    def w(self):\n"
        "        self.x = 1\n"
        "    def r(self):\n"
        "        return self.x\n",
        encoding="utf-8",
    )
    DataFlowEngine(DataFlowStore(open_store(tmp_path))).scan(tmp_path)


def test_writers_tool(tmp_path: Path) -> None:
    _prepare(tmp_path)
    res = asyncio.run(mcp.forgeos_writers("A.x", project=str(tmp_path)))
    assert any(w["id"] == "func:m.py#A.w" for w in res["writers"])


def test_readers_tool(tmp_path: Path) -> None:
    _prepare(tmp_path)
    res = asyncio.run(mcp.forgeos_readers("A.x", project=str(tmp_path)))
    assert any(r["id"] == "func:m.py#A.r" for r in res["readers"])


def test_missing_state_errors(tmp_path: Path) -> None:
    _prepare(tmp_path)
    res = asyncio.run(mcp.forgeos_writers("Nope.nope", project=str(tmp_path)))
    assert "error" in res
