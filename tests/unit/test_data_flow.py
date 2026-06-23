from __future__ import annotations

from pathlib import Path

from forgeos.core.dataflow_intel import DataFlowEngine, DataFlowStore
from forgeos.core.dataflow_intel.query import data_flow, readers, writers
from forgeos.core.exec_intel import ExecGraphStore, ExecIntelEngine
from forgeos.testing.fakes import InMemoryStorage

_SRC = (
    "class A:\n"
    "    def w(self):\n"
    "        self.x = 1\n"
    "    def r(self):\n"
    "        return self.x\n"
)


def test_readers_and_writers(tmp_path: Path) -> None:
    (tmp_path / "m.py").write_text(_SRC, encoding="utf-8")
    store = InMemoryStorage()
    df = DataFlowStore(store)
    DataFlowEngine(df).scan(tmp_path)
    assert writers(df, "state:m.py#A.x") == ["func:m.py#A.w"]
    assert readers(df, "state:m.py#A.x") == ["func:m.py#A.r"]


def test_data_flow_includes_callers(tmp_path: Path) -> None:
    (tmp_path / "m.py").write_text(
        _SRC + "\ndef caller():\n    A().w\n", encoding="utf-8"
    )
    store = InMemoryStorage()
    ExecIntelEngine(ExecGraphStore(store)).scan(tmp_path)
    df = DataFlowStore(store)
    DataFlowEngine(df).scan(tmp_path)
    flow = data_flow(df, ExecGraphStore(store), "state:m.py#A.x")
    assert "func:m.py#A.w" in flow["upstream"]
    assert "func:m.py#A.r" in flow["downstream"]
