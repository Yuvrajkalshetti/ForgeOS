from __future__ import annotations

import asyncio
from pathlib import Path

from forgeos.adapters.transport.cli._shared import open_store
from forgeos.adapters.transport.mcp import server as mcp
from forgeos.core.dataflow_intel import DataFlowEngine, DataFlowStore
from forgeos.core.dataflow_intel.lineage import find_paths, forward_adjacency
from forgeos.core.exec_intel import ExecGraphStore, ExecIntelEngine
from forgeos.core.exec_intel.models import Confidence
from forgeos.testing.fakes import InMemoryStorage

_SRC = (
    "class State:\n"
    "    val: int\n\n"
    "class Producer:\n"
    "    def write(self, s: State) -> None:\n"
    "        s.val = 1\n\n"
    "class Consumer:\n"
    "    def read(self, s: State) -> int:\n"
    "        return s.val\n"
)


def test_forward_path_through_state(tmp_path: Path) -> None:
    (tmp_path / "m.py").write_text(_SRC, encoding="utf-8")
    store = InMemoryStorage()
    ExecIntelEngine(ExecGraphStore(store)).scan(tmp_path)
    DataFlowEngine(DataFlowStore(store)).scan(tmp_path)
    adj = forward_adjacency(ExecGraphStore(store), DataFlowStore(store), Confidence.RESOLVED)
    paths = find_paths(adj, "func:m.py#Producer.write", "func:m.py#Consumer.read", 8, 10)
    assert any(
        p[0] == "func:m.py#Producer.write" and p[-1] == "func:m.py#Consumer.read" for p in paths
    )
    assert any("state:m.py#State.val" in p for p in paths)


def test_lineage_tool_with_anchor(tmp_path: Path) -> None:
    (tmp_path / ".forgeos").mkdir()
    (tmp_path / ".forgeos" / "dataflow.yaml").write_text(
        "anchors:\n  WRITE: Producer.write\n  READ: Consumer.read\n", encoding="utf-8"
    )
    (tmp_path / "m.py").write_text(_SRC, encoding="utf-8")
    store = open_store(tmp_path)
    ExecIntelEngine(ExecGraphStore(store)).scan(tmp_path)
    DataFlowEngine(DataFlowStore(store)).scan(tmp_path)
    res = asyncio.run(mcp.forgeos_lineage("WRITE", "READ", project=str(tmp_path)))
    assert res["source"] == "func:m.py#Producer.write"
    assert res["paths"]


def test_lineage_missing_endpoint(tmp_path: Path) -> None:
    (tmp_path / "m.py").write_text(_SRC, encoding="utf-8")
    open_store(tmp_path)
    res = asyncio.run(mcp.forgeos_lineage("Nope", "AlsoNope", project=str(tmp_path)))
    assert "error" in res
