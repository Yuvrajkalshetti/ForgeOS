from __future__ import annotations

import asyncio
from pathlib import Path

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.adapters.transport.mcp import server as mcp
from forgeos.core.exec_intel import ExecGraphStore, ExecIntelEngine


def _prepare(tmp_path: Path) -> None:
    (tmp_path / "m.py").write_text("def g():\n    pass\n\ndef f():\n    g()\n", encoding="utf-8")
    ExecIntelEngine(ExecGraphStore(open_store(tmp_path))).scan(tmp_path)


def test_symbol_search(tmp_path: Path) -> None:
    _prepare(tmp_path)
    found = asyncio.run(mcp.forgeos_symbol("f", project=str(tmp_path)))
    assert any(s["label"] == "f" for s in found)


def test_call_graph_callees(tmp_path: Path) -> None:
    _prepare(tmp_path)
    res = asyncio.run(mcp.forgeos_call_graph("func:m.py#f", project=str(tmp_path)))
    assert any(s["id"] == "func:m.py#g" for s in res["symbols"])


def test_impact_analysis(tmp_path: Path) -> None:
    _prepare(tmp_path)
    res = asyncio.run(mcp.forgeos_impact_analysis("func:m.py#g", project=str(tmp_path)))
    assert any(s["id"] == "func:m.py#f" for s in res["dependents"])


def test_paths_to(tmp_path: Path) -> None:
    _prepare(tmp_path)
    res = asyncio.run(mcp.forgeos_paths_to("func:m.py#g", project=str(tmp_path)))
    flat = [[s["id"] for s in chain] for chain in res["paths"]]
    assert ["func:m.py#f", "func:m.py#g"] in flat


def test_missing_symbol_errors(tmp_path: Path) -> None:
    _prepare(tmp_path)
    res = asyncio.run(mcp.forgeos_call_graph("nope", project=str(tmp_path)))
    assert "error" in res
